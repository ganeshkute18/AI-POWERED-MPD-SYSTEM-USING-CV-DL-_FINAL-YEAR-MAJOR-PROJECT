"""
Flask Backend API for Missing Person Detection
Handles face embedding computation and storage using DeepFace
"""

import os
import sys
import json
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import threading
import base64
import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import time

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class AlertSystem:
    """Enhanced alert system for sending notifications when missing persons are detected"""
    
    def __init__(self):
        self.alerts_sent = set()  # Track sent alerts to avoid spam (time bucket key)
        self.last_alert_times = {}  # Precise per-person/camera timestamp for cooldown
        self.alert_cooldown = 30  # 30 seconds cooldown between alerts for same person/camera
        self.alert_threshold = 0.55  # Minimum similarity to trigger audible alert (strong matches)
        self.alerts_history = []  # Store alert history
        self.snapshots_folder = 'snapshots'
        self.alerts_folder = 'alerts'
        
        # Create necessary directories
        os.makedirs(self.snapshots_folder, exist_ok=True)
        os.makedirs(self.alerts_folder, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.alerts_folder, 'alerts.log')),
                logging.StreamHandler()
            ]
        )
        logging.getLogger().setLevel(logging.WARNING)
    
    def save_snapshot(self, frame, match_data, camera_source=None):
        """
        Save snapshot of detected person
        
        Args:
            frame: numpy array of the frame
            match_data: dict with match information
            camera_source: source identifier for the camera
        """
        try:
            timestamp = datetime.now()
            person_name = match_data['name']
            confidence = match_data.get('similarity', 0)
            
            # Create filename with timestamp and person name
            safe_name = "".join(c for c in person_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_name}_{confidence:.2f}.jpg"
            if camera_source:
                filename = f"{camera_source}_{filename}"
            
            filepath = os.path.join(self.snapshots_folder, filename)
            
            # Draw bounding box and label on snapshot if available
            annotated_frame = frame.copy()
            if 'bbox' in match_data:
                bbox = match_data['bbox']
                x, y, w, h = bbox
                cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                label = f"{person_name} ({confidence*100:.1f}%)"
                cv2.putText(annotated_frame, label, (x, y - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Save snapshot
            # cv2.imwrite(filepath, annotated_frame)
            return filepath
        except Exception as e:
            logging.error(f"Error saving snapshot: {e}")
            return None
    
    def send_alert(self, match_data, frame=None, frame_info=None, camera_source=None):
        """
        Send comprehensive alert for detected missing person with snapshot
        
        Args:
            match_data: dict with match information
            frame: numpy array of the frame (for snapshot)
            frame_info: optional frame information
            camera_source: source identifier for the camera
        """
        person_name = match_data['name']
        confidence = match_data.get('similarity', match_data.get('confidence', '0%'))
        if isinstance(confidence, str):
            confidence_val = float(confidence.replace('%', '')) / 100
        else:
            confidence_val = float(confidence)
        
        timestamp = datetime.now().isoformat()
        
# Enforce strong-match threshold before alerting
        if confidence_val < self.alert_threshold:
            logging.debug(f"[ALERT SKIP] {person_name}: similarity {confidence_val:.2f} < threshold {self.alert_threshold:.2f}")
            return

        # Check if we recently sent an alert for this person+camera (cooldown)
        base_key = f"{person_name}_{camera_source}"
        current_time = datetime.now().timestamp()

        last_time = self.last_alert_times.get(base_key, 0)
        if current_time - last_time < self.alert_cooldown:
            logging.debug(f"[ALERT SKIP] {person_name}: cooldown active ({current_time-last_time:.1f}s < {self.alert_cooldown}s)")
            return

        self.last_alert_times[base_key] = current_time

        alert_bucket_key = f"{person_name}_{camera_source}_{int(current_time // self.alert_cooldown)}"
        self.alerts_sent.add(alert_bucket_key)

        # Clean old alerts (keep only recent bucket keys within last hour)
        cutoff = current_time - 3600
        self.alerts_sent = {k for k in self.alerts_sent 
                            if int(k.split('_')[-1]) * self.alert_cooldown > cutoff}
        self.last_alert_times = {k: v for k, v in self.last_alert_times.items() if v > cutoff}

        logging.debug(f"[ALERT TRIGGER] {person_name} ({confidence_val*100:.2f}%) - base_key: {base_key}")
        
        # Save snapshot if frame is provided
        snapshot_path = None
        if frame is not None:
            snapshot_path = self.save_snapshot(frame, match_data, camera_source)
        
        # Create alert record
        alert_record = {
            'person_name': person_name,
            'confidence': confidence_val,
            'confidence_str': f"{confidence_val * 100:.2f}%",
            'timestamp': timestamp,
            'camera_source': camera_source or 'unknown',
            'snapshot_path': snapshot_path,
            'frame_info': frame_info or {}
        }
        
        # Add to history
        self.alerts_history.append(alert_record)
        if len(self.alerts_history) > 1000:  # Keep last 1000 alerts
            self.alerts_history = self.alerts_history[-1000:]
        
        # Log alert
        logging.warning(f"ALERT: Missing person '{person_name}' detected with {confidence_val*100:.2f}% confidence at {timestamp} (Camera: {camera_source})")
        
        # Send system notification
        self._send_system_alert(alert_record)
        
        # Emit alert via WebSocket with snapshot
        alert_data = {
            'person_name': person_name,
            'confidence': f"{confidence_val * 100:.2f}%",
            'confidence_value': confidence_val,
            'timestamp': timestamp,
            'camera_source': camera_source or 'unknown',
            'message': f"🚨 ALERT: {person_name} detected!",
            'snapshot_path': snapshot_path,
            'snapshot_url': f'/api/snapshots/{os.path.basename(snapshot_path)}' if snapshot_path else None
        }
        
        try:
            logging.debug(f"[SOCKETIO] Emitting alert_triggered for {person_name}")
            socketio.emit('alert_triggered', alert_data, broadcast=True)
            logging.debug("[SOCKETIO] Alert emitted successfully")
        except Exception as e:
            logging.error(f"[SOCKETIO ERROR] Failed to emit alert: {e}")
        
        return alert_record
    
    def _send_system_alert(self, alert_record):
        """Send system alert with comprehensive information"""
        try:
            alert_message = f"""
{'='*60}
🚨 MISSING PERSON ALERT 🚨
{'='*60}

Person Detected: {alert_record['person_name']}
Confidence: {alert_record['confidence_str']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Camera Source: {alert_record['camera_source']}
Snapshot: {alert_record['snapshot_path'] or 'Not available'}

Please check the live feed immediately!
{'='*60}
"""
            print(alert_message)
            
            # TODO: Integrate with email service (SendGrid, SMTP) or SMS (Twilio)
            # Example: self._send_email_alert(alert_record)
            # Example: self._send_sms_alert(alert_record)
            
        except Exception as e:
            logging.error(f"Error sending system alert: {e}")
    
    def get_alert_history(self, limit=50, person_name=None):
        """Get alert history with optional filtering"""
        history = self.alerts_history.copy()
        
        if person_name:
            history = [a for a in history if a['person_name'].lower() == person_name.lower()]
        
        return history[-limit:] if history else []
    
    def get_snapshot(self, filename):
        """Get snapshot file path"""
        filepath = os.path.join(self.snapshots_folder, filename)
        if os.path.exists(filepath):
            return filepath
        return None


# Initialize alert system
alert_system = AlertSystem()

# Match dedupe and throttling across frames
match_emit_cooldown = 10  # seconds cooldown per person + camera
match_last_emitted = {}

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False
)
# ================== ArcFace Registration Model ==================
# This model will be used when user uploads a missing person photo

from insightface.app import FaceAnalysis


def _gpu_available():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


gpu_available = _gpu_available()
providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if gpu_available else ["CPUExecutionProvider"]
print("Loading ArcFace model for registration (database embeddings)...")
print(f"ArcFace registration GPU available: {gpu_available} | providers: {providers}")

arcface_model = FaceAnalysis(
    name="buffalo_l",
    providers=providers
)

arcface_model.prepare(ctx_id=0 if gpu_available else -1, det_size=(640, 640))

print("ArcFace registration model loaded successfully")


# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
EMBEDDINGS_FILE = 'stored_embeddings.json'
EVIDENCE_FOLDER = 'evidence'
AUDIT_LOG_FILE = 'audit.log'
# Path to configured CCTV/Drone streams (project root / streams / cameras.json)
STREAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'streams'))
CAMERAS_CONFIG_FILE = os.path.join(STREAMS_DIR, 'cameras.json')

# Create evidence directory
os.makedirs(EVIDENCE_FOLDER, exist_ok=True)

# Import real-time detector (after configuration)
from realtime_detector import RealTimeDetector, VideoStreamProcessor

# Initialize real-time detector (use absolute path to trained model `best.pt` in backend dir)
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.pt')
print(f"Using YOLO model path: {MODEL_PATH}")
realtime_detector = RealTimeDetector(embeddings_file=EMBEDDINGS_FILE, threshold=0.30, frame_skip=1, model_path=MODEL_PATH)
stream_processor = VideoStreamProcessor(realtime_detector)
processing_thread = None

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set maximum file size (16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def stream_callback(result, frame):

    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    socketio.emit('frame_update', {
        'frame': jpg_as_text
    })

    if result["matches"]:
        socketio.emit("match_found", {
            "matches": result["matches"],
            "timestamp": datetime.now().isoformat()
        })
        
def start_stream_thread(source, camera_name):

    global processing_thread

    def run():
        stream_processor.open_camera(source, camera_name)
        stream_processor.process_stream(callback=stream_callback)

    processing_thread = threading.Thread(target=run)
    processing_thread.daemon = True
    processing_thread.start()
        



def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_embeddings():
    """Load stored embeddings from JSON file"""
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            with open(EMBEDDINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            print(f"Error loading embeddings: {e}")
            return {}
    return {}


def save_embeddings(embeddings_dict):
    """Save embeddings dictionary to JSON file"""
    try:
        with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(embeddings_dict, f, indent=2, ensure_ascii=False, default=str)
        return True
    except (IOError, UnicodeEncodeError) as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"Error saving embeddings: {error_msg}")
        return False

def compute_face_embedding(image_path):
    """
    Generate ArcFace embedding for missing person registration
    """

    try:
        img = cv2.imread(image_path)

        if img is None:
            print("Image could not be read")
            return None

        # Detect face and generate embedding
        faces = arcface_model.get(img)

        if len(faces) == 0:
            print("No face detected in uploaded image")
            return None

        embedding = faces[0].embedding

        # Normalize embedding (CRITICAL for cosine similarity)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    except Exception as e:
        print("ArcFace registration error:", e)
        return None


def find_matching_person(detected_embedding, threshold=0.6):
    """
    Find matching person from stored embeddings using cosine similarity
    Returns list of matches with similarity scores
    """
    embeddings_dict = load_embeddings()
    matches = []
    
    if not embeddings_dict:
        return matches
    
    detected_embedding_np = np.array(detected_embedding).reshape(1, -1)
    
    for name, data in embeddings_dict.items():
        stored_embedding = np.array(data.get('embedding')).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(detected_embedding_np, stored_embedding)[0][0]
        
        if similarity >= threshold:
            matches.append({
                'name': name,
                'similarity': float(similarity),
                'confidence': f"{similarity * 100:.2f}%",
                'created_at': data.get('created_at')
            })
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches


@app.route('/target_person', methods=['POST'])
def add_target_person():
    """
    POST endpoint to add a missing person
    Accepts form data: 'name' (string) and 'image' (file upload)
    Returns JSON response with success status
    """
    # Check if name is provided
    if 'name' not in request.form:
        return jsonify({
            'success': False,
            'error': 'Missing required field: name'
        }), 400
    
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Missing required field: image'
        }), 400
    
    name = request.form['name'].strip()
    image_file = request.files['image']
    
    # Validate name
    if not name:
        return jsonify({
            'success': False,
            'error': 'Name cannot be empty'
        }), 400
    
    # Validate file
    if image_file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Save uploaded file temporarily
    filename = secure_filename(image_file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        image_file.save(filepath)
        
        # Compute face embedding
        embedding = compute_face_embedding(filepath)
        
        if embedding is None:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': 'No face detected in the image. Please ensure:\n' +
                         '1. The image contains a clear, front-facing face\n' +
                         '2. The face is well-lit and not obscured\n' +
                         '3. The image is not too blurry or low quality\n' +
                         '4. Try a different image with better lighting and angle'
            }), 400
        
        # Load existing embeddings
        embeddings_dict = load_embeddings()
        
        # Check if name already exists
        if name in embeddings_dict:
            return jsonify({
                'success': False,
                'error': f'Person with name "{name}" already exists. Use a different name or update existing entry.'
            }), 409
        
        # Store embedding with metadata
        # Normalize embedding and store metadata
        try:
            emb_np = np.array(embedding, dtype=float)
            norm = np.linalg.norm(emb_np)
            if norm > 0:
                emb_np = (emb_np / norm).tolist()
            else:
                emb_np = emb_np.tolist()
        except Exception:
            emb_np = embedding

        embeddings_dict[name] = {
            'embedding': emb_np,
            'created_at': datetime.now().isoformat(),
            'image_filename': unique_filename,
            'uploader_ip': request.remote_addr,
            'source': 'manual_upload'
        }
        
        # Save embeddings
        if save_embeddings(embeddings_dict):
            # Reload embeddings in real-time detector so new person is immediately available
            try:
                realtime_detector.reload_embeddings()
                print(f"Reloaded embeddings. Total persons in database: {len(realtime_detector.stored_embeddings)}")
            except Exception as e:
                print(f"Warning: Could not reload embeddings in real-time detector: {e}")
            
            # Log audit event
            log_audit_event(
                'PERSON_ADDED',
                f'Added missing person: {name}',
                details={'name': name, 'image_file': unique_filename}
            )
            
            return jsonify({
                'success': True,
                'name': name,
                'message': f'Successfully added missing person: {name}. Person is now available for real-time detection!',
                'total_persons': len(embeddings_dict),
                'ready_for_detection': True
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save embedding'
            }), 500
            
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        # Safely encode error message
        error_msg = str(e)
        try:
            # Try to encode to ASCII, replacing problematic characters
            error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
        except:
            error_msg = "An error occurred while processing the request"
        return jsonify({
            'success': False,
            'error': f'Server error: {error_msg}'
        }), 500


@app.route('/targets', methods=['GET'])
def get_targets():
    """
    GET endpoint to retrieve all stored missing persons
    Returns JSON with list of names and their embeddings
    """
    try:
        embeddings_dict = load_embeddings()
        
        # Format response with names and embeddings
        targets = []
        for name, data in embeddings_dict.items():
            targets.append({
                'name': name,
                'embedding': data.get('embedding'),
                'created_at': data.get('created_at'),
                'image_filename': data.get('image_filename')
            })
        
        return jsonify({
            'success': True,
            'count': len(targets),
            'targets': targets
        }), 200
        
    except Exception as e:
        # Safely encode error message
        error_msg = str(e)
        try:
            error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
        except:
            error_msg = "An error occurred while retrieving targets"
        return jsonify({
            'success': False,
            'error': f'Error retrieving targets: {error_msg}'
        }), 500


@app.route('/target_person/<name>', methods=['DELETE'])
def delete_target_person(name):
    """
    DELETE endpoint to remove a missing person by name
    Returns JSON response with success status
    """
    try:
        from urllib.parse import unquote
        person_name = unquote(name)
        
        embeddings_dict = load_embeddings()
        
        if person_name not in embeddings_dict:
            return jsonify({
                'success': False,
                'error': f'Person "{person_name}" not found in database'
            }), 404
        
        # Delete the person
        deleted_data = embeddings_dict.pop(person_name)
        
        # Save updated embeddings
        if save_embeddings(embeddings_dict):
            # Reload embeddings in real-time detector
            try:
                realtime_detector.reload_embeddings()
            except Exception as e:
                print(f"Warning: Could not reload embeddings after deletion: {e}")
            
            # Log audit event
            log_audit_event(
                'PERSON_DELETED',
                f'Removed missing person: {person_name}',
                details={'name': person_name, 'image_file': deleted_data.get('image_filename')}
            )
            
            return jsonify({
                'success': True,
                'message': f'Successfully removed missing person: {person_name}',
                'total_persons': len(embeddings_dict)
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save embeddings after deletion'
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        try:
            error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
        except:
            error_msg = "An error occurred while deleting the person"
        return jsonify({
            'success': False,
            'error': f'Server error: {error_msg}'
        }), 500


def find_matching_person(detected_embedding, threshold=0.6):
    """
    Find matching person from stored embeddings using cosine similarity
    Returns list of matches with similarity scores
    """
    embeddings_dict = load_embeddings()
    matches = []
    
    if not embeddings_dict:
        return matches
    
    detected_embedding_np = np.array(detected_embedding).reshape(1, -1)
    
    for name, data in embeddings_dict.items():
        stored_embedding = np.array(data.get('embedding')).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(detected_embedding_np, stored_embedding)[0][0]
        
        if similarity >= threshold:
            matches.append({
                'name': name,
                'similarity': float(similarity),
                'confidence': f"{similarity * 100:.2f}%",
                'created_at': data.get('created_at')
            })
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches


@app.route('/detect', methods=['POST'])
def detect_person():
    """
    POST endpoint to detect a person from camera/image
    Accepts form data: 'image' (file upload or base64)
    Returns JSON with matched persons if found
    """
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Missing required field: image'
        }), 400
    
    image_file = request.files['image']
    
    # Validate file
    if image_file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    # Save uploaded file temporarily
    filename = secure_filename(image_file.filename) if image_file.filename else 'camera_capture.jpg'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"detect_{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        image_file.save(filepath)
        
        # Compute face embedding
        embedding = compute_face_embedding(filepath)
        
        if embedding is None:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': 'No face detected in the image.'
            }), 400
        
        # Find matching persons
        matches = find_matching_person(embedding, threshold=0.6)
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if matches:
            return jsonify({
                'success': True,
                'matches': matches,
                'message': f'Found {len(matches)} potential match(es)'
            }), 200
        else:
            return jsonify({
                'success': True,
                'matches': [],
                'message': 'No matching person found in database'
            }), 200
            
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        error_msg = str(e)
        try:
            error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
        except:
            error_msg = "An error occurred while processing the detection"
        return jsonify({
            'success': False,
            'error': f'Server error: {error_msg}'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Missing Person Detection API'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Serve the HTML frontend"""
    return render_template('index.html')


@app.route('/camera', methods=['GET'])
def camera_page():
    """Serve the camera detection page"""
    return render_template('camera.html')


@app.route('/realtime', methods=['GET'])
def realtime_page():
    """Serve the real-time detection dashboard"""
    return render_template('realtime.html')


@app.route('/admin', methods=['GET'])
def admin_page():
    """Serve the admin panel dashboard"""
    return render_template('admin.html')


@app.route('/instructions', methods=['GET'])
def instructions_page():
    """Serve the instructions page"""
    return render_template('instructions.html')


def load_configured_cameras():
    """Load CCTV/Drone cameras from streams/cameras.json."""
    try:
        if os.path.exists(CAMERAS_CONFIG_FILE):
            with open(CAMERAS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('cameras', [])
    except Exception as e:
        print(f"Error loading cameras config: {e}")
    return []


def save_configured_cameras(cameras_list):
    """Save CCTV/Drone cameras to streams/cameras.json."""
    try:
        os.makedirs(STREAMS_DIR, exist_ok=True)
        with open(CAMERAS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'cameras': cameras_list}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving cameras config: {e}")
    return False


@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """Start real-time video stream processing with enhanced detection"""
    global processing_thread, stream_processor
    
    data = request.json or {}
    source = data.get('source', 0)  # 0 for default webcam, or RTSP URL, IP camera, etc.
    # Ensure webcam index is int (frontend may send string "0")
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    camera_name = data.get('camera_name', str(source))  # Human-readable camera name    
    try:
        # Set detection backend for robustness (e.g. RetinaFace for CCTV/drone)
       
        
        # Stop any existing stream first - with proper cleanup
        if stream_processor.is_processing:
            print(f"Stopping existing stream from: {stream_processor.camera_name}")
            stream_processor.stop()
            time.sleep(1.5)  # Increased wait time to ensure full cleanup and camera release
            
            # Wait for processing thread to finish
            if processing_thread and processing_thread.is_alive():
                processing_thread.join(timeout=3)
                time.sleep(0.5)  # Extra time for OS to release camera resource
        
        # Reload embeddings in case new persons were added
        realtime_detector.reload_embeddings()
        
        # Open camera source with name
        if stream_processor.open_camera(source, camera_name=camera_name):
            # Start processing in background thread
            def process_with_callback():

                def callback(result, annotated_frame):

                    matches = result.get('matches', [])

                    # ---------- ALERT SYSTEM (only on strong matches) ----------
                    if matches:
                        for match in matches:
                            sim = match.get('similarity', 0)
                            
                            # Only process alerts for strong matches (reduce spam)
                            if sim >= alert_system.alert_threshold:
                                # Alert system has its own cooldown - will skip repeated alerts
                                alert_system.send_alert(
                                    match,
                                    frame=annotated_frame,
                                    frame_info={
                                        'frame': result.get('frame', 0),
                                        'faces_detected': result.get('faces_detected', 0),
                                        'total_matches': len(matches),
                                        'match_type': 'strong' if sim >= 0.55 else 'weak'
                                    },
                                    camera_source=camera_name
                                )

                    # ---------- SEND MATCH DATA (deduplicated/throttled) ----------
                    if matches:
                        deduped_matches = []
                        seen_names = set()
                        now_ts = datetime.now().timestamp()

                        for match in matches:
                            name = match.get('name', 'unknown')
                            if name in seen_names:
                                continue
                            seen_names.add(name)

                            key = f"{name}_{camera_name}"
                            last_emitted = match_last_emitted.get(key, 0)
                            if now_ts - last_emitted >= match_emit_cooldown:
                                deduped_matches.append(match)
                                match_last_emitted[key] = now_ts

                        if deduped_matches:
                            socketio.emit('match_found', {
                                'matches': deduped_matches,
                                'timestamp': datetime.now().isoformat(),
                                'faces_detected': result.get('faces_detected', 0),
                                'camera_source': camera_name
                            })

                    # ---------- SEND FRAME ----------
                    try:
                        ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ret:
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            socketio.emit('frame_update', {
                                'frame': frame_base64,
                                'timestamp': datetime.now().isoformat(),
                                'camera_source': camera_name,
                                'fps': getattr(stream_processor, 'fps', 0.0)
                            })
                    except Exception as e:
                        print(f"[STREAM ERROR] Frame encoding failed: {e}")

                stream_processor.process_stream(callback)

            
            processing_thread = threading.Thread(target=process_with_callback, daemon=True)
            processing_thread.start()
            
            return jsonify({
                'success': True,
                'message': f'Stream started from source: {source}',
                'camera_name': camera_name,
                'stored_persons': len(realtime_detector.stored_embeddings)
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to open camera source'
            }), 400
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"Error starting stream: {error_msg}")
        return jsonify({
            'success': False,
            'error': f'{error_msg}. Make sure the camera is not in use by another application and you have proper permissions.',
            'details': str(e)
        }), 500


@app.route('/api/stream/stop', methods=['POST'])
def stop_stream():
    global stream_processor

    try:
        if stream_processor:
            stream_processor.stop()

        socketio.emit('stream_stopped', {'success': True})
        return jsonify({'success': True})

    except Exception as e:
        print("STOP ERROR:", e)
        return jsonify({'success': False, 'error': str(e)}), 200

    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error stopping stream: {error_msg}'
        }), 500


@app.route('/api/stream/status', methods=['GET'])
def stream_status():
    """Get current stream status"""
    return jsonify({
        'success': True,
        'is_processing': stream_processor.is_processing,
        'current_source': stream_processor.current_source,
        'detection_backend': getattr(realtime_detector, 'detection_backend', 'opencv'),
        'stored_persons': len(realtime_detector.stored_embeddings),
        'recent_matches': realtime_detector.get_recent_matches(5),
        'fps': getattr(stream_processor, 'fps', 0.0),
        'last_frame_time': getattr(stream_processor, 'last_frame_time', None),
        'health_status': getattr(stream_processor, 'health_status', 'unknown')
    }), 200


@app.route('/api/stream/reload', methods=['POST'])
def reload_embeddings():
    """Reload stored embeddings"""
    try:
        realtime_detector.reload_embeddings()
        return jsonify({
            'success': True,
            'message': f'Reloaded {len(realtime_detector.stored_embeddings)} embeddings'
        }), 200
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error reloading: {error_msg}'
        }), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        person_name = request.args.get('person_name', None)
        
        history = alert_system.get_alert_history(limit=limit, person_name=person_name)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'alerts': history
        }), 200
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error retrieving alert history: {error_msg}'
        }), 500


@app.route('/api/snapshots/<filename>', methods=['GET'])
def get_snapshot(filename):
    """Get snapshot image"""
    try:
        filepath = alert_system.get_snapshot(filename)
        if filepath and os.path.exists(filepath):
            return Response(
                open(filepath, 'rb').read(),
                mimetype='image/jpeg',
                headers={'Content-Disposition': f'inline; filename={filename}'}
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Snapshot not found'
            }), 404
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error retrieving snapshot: {error_msg}'
        }), 500


@app.route('/api/cameras', methods=['GET'])
def list_cameras():
    """List available camera sources: webcams + configured CCTV/Drone from cameras.json"""
    try:
        available_cameras = []
        
        # 1. Test webcam indices 0-3
        for i in range(4):
            test_cap = None
            try:
                if sys.platform == 'win32':
                    test_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                else:
                    test_cap = cv2.VideoCapture(i)
                
                if test_cap.isOpened():
                    ret, frame = test_cap.read()
                    if ret:
                        available_cameras.append({
                            'id': f'webcam_{i}',
                            'name': f'Webcam {i}',
                            'source': i,
                            'type': 'webcam',
                            'status': 'available'
                        })
                test_cap.release()
            except Exception:
                if test_cap:
                    test_cap.release()
                continue
        
        if not any(c.get('type') == 'webcam' for c in available_cameras):
            available_cameras.insert(0, {
                'id': 'webcam_0',
                'name': 'Default Webcam (try this)',
                'source': 0,
                'type': 'webcam',
                'status': 'unknown - may need testing'
            })
        
        # 2. Add configured CCTV and Drone streams from cameras.json
        configured = load_configured_cameras()
        for cam in configured:
            cid = cam.get('id') or f"{cam.get('type', 'stream')}_{len(available_cameras)}"
            available_cameras.append({
                'id': cid,
                'name': cam.get('name', cid),
                'source': cam.get('source') or cam.get('url', ''),
                'type': cam.get('type', 'cctv'),  # 'cctv' or 'drone'
                'status': cam.get('status', 'configured')
            })
        
        return jsonify({
            'success': True,
            'cameras': available_cameras,
            'count': len(available_cameras),
            'message': f'Found {len(available_cameras)} camera(s)'
        }), 200
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error listing cameras: {error_msg}'
        }), 500


@app.route('/api/cameras/save', methods=['POST'])
def save_camera():
    """Add a CCTV or Drone stream to cameras.json and return updated list."""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        source = data.get('source') or data.get('url', '')
        stream_type = (data.get('type') or 'cctv').lower()
        if stream_type not in ('cctv', 'drone'):
            stream_type = 'cctv'
        if not name or not source:
            return jsonify({
                'success': False,
                'error': 'name and source (or url) are required'
            }), 400
        cameras = load_configured_cameras()
        cam_id = f"{stream_type}_{name.replace(' ', '_')}_{len(cameras)}"
        cameras.append({
            'id': cam_id,
            'name': name,
            'source': source,
            'type': stream_type,
            'status': 'configured'
        })
        if save_configured_cameras(cameras):
            return jsonify({
                'success': True,
                'message': f'Added {stream_type}: {name}',
                'cameras': cameras
            }), 200
        return jsonify({'success': False, 'error': 'Failed to save cameras config'}), 500
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/cameras/test', methods=['POST'])
def test_camera():
    """Test if a camera source can be opened"""
    try:
        data = request.json or {}
        source = data.get('source', 0)
        
        test_cap = None
        try:
            if isinstance(source, str):
                test_cap = cv2.VideoCapture(source)
            else:
                if sys.platform == 'win32':
                    test_cap = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
                else:
                    test_cap = cv2.VideoCapture(int(source))
            
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret:
                    test_cap.release()
                    return jsonify({
                        'success': True,
                        'message': f'Camera {source} is available and working',
                        'source': source
                    }), 200
                else:
                    test_cap.release()
                    return jsonify({
                        'success': False,
                        'error': f'Camera {source} opened but cannot read frames'
                    }), 400
            else:
                if test_cap:
                    test_cap.release()
                return jsonify({
                    'success': False,
                    'error': f'Cannot open camera {source}. Make sure it is not in use by another application.'
                }), 400
        except Exception as e:
            if test_cap:
                test_cap.release()
            raise e
            
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error testing camera: {error_msg}'
        }), 500


@app.route('/api/evidence', methods=['GET'])
def get_evidence():
    """Get evidence collection (snapshots and alerts)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        person_name = request.args.get('person_name', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        # Get alerts as evidence
        alerts = alert_system.get_alert_history(limit=limit, person_name=person_name)
        
        # Filter by date if provided
        if start_date or end_date:
            filtered_alerts = []
            for alert in alerts:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if start_date:
                    start = datetime.fromisoformat(start_date)
                    if alert_time < start:
                        continue
                if end_date:
                    end = datetime.fromisoformat(end_date)
                    if alert_time > end:
                        continue
                filtered_alerts.append(alert)
            alerts = filtered_alerts
        
        return jsonify({
            'success': True,
            'count': len(alerts),
            'evidence': alerts
        }), 200
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error retrieving evidence: {error_msg}'
        }), 500


def log_audit_event(event_type, description, user=None, details=None):
    """Log audit events for law enforcement compliance"""
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'description': description,
            'user': user or 'system',
            'details': details or {}
        }
        
        # Write to audit log file
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logging.info(f"AUDIT: {event_type} - {description}")
    except Exception as e:
        logging.error(f"Error logging audit event: {e}")


@app.route('/api/audit', methods=['GET'])
def get_audit_log():
    """Get audit log for compliance"""
    try:
        limit = request.args.get('limit', 100, type=int)
        event_type = request.args.get('event_type', None)
        
        audit_entries = []
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        entry = json.loads(line.strip())
                        if event_type is None or entry.get('event_type') == event_type:
                            audit_entries.append(entry)
                    except:
                        continue
        
        return jsonify({
            'success': True,
            'count': len(audit_entries),
            'audit_log': audit_entries
        }), 200
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        return jsonify({
            'success': False,
            'error': f'Error retrieving audit log: {error_msg}'
        }), 500


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'message': 'Connected to real-time detection server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    # Run Flask app with SocketIO
    print("Starting Missing Person Detection API...")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Embeddings file: {os.path.abspath(EMBEDDINGS_FILE)}")
    print("Real-time detection enabled")


@app.route('/api/test/yolo', methods=['GET'])
def test_yolo():
    """Quick test to see if YOLO detects faces on default webcam"""
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'success': False, 'error': 'Cannot read from webcam'}), 400
        
        faces = realtime_detector.detect_faces(frame)
        return jsonify({
            'success': True,
            'faces_detected': len(faces),
            'frame_shape': frame.shape,
            'message': f'YOLO detected {len(faces)} face(s)'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test/embedding', methods=['GET'])
def test_embedding():
    """Test face embedding matching against stored persons"""
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'success': False, 'error': 'Cannot read from webcam'}), 400
        
        # Detect face
        faces = realtime_detector.detect_faces(frame)
        if len(faces) == 0:
            return jsonify({'success': False, 'error': 'No face detected by YOLO'}), 400
        
        # Get embedding for first face
        face_img = faces[0]['face']
        embedding = realtime_detector.get_embedding(face_img)
        
        if embedding is None:
            return jsonify({'success': False, 'error': 'ArcFace failed to generate embedding'}), 400
        
        # Compare with stored embeddings
        embeddings_dict = load_embeddings()
        results = {}
        
        for name, data in embeddings_dict.items():
            stored_emb = np.array(data.get('embedding')).reshape(1, -1)
            live_emb = embedding.reshape(1, -1)
            similarity = float(cosine_similarity(live_emb, stored_emb)[0][0])
            results[name] = {
                'similarity': similarity,
                'percentage': f'{similarity*100:.2f}%',
                'matches': similarity >= 0.30
            }
        
        return jsonify({
            'success': True,
            'message': 'Embedding comparison complete',
            'face_detected': True,
            'embedding_generated': True,
            'stored_persons': results,
            'threshold': 0.30
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5001,
        debug=False,
        allow_unsafe_werkzeug=True
    )

