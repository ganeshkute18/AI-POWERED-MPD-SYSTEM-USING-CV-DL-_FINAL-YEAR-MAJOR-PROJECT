import cv2
import sys
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import threading
import time as tm
from datetime import datetime
import logging

# ==============================
# REAL TIME FACE DETECTOR
# ==============================

class RealTimeDetector:

    def __init__(self, embeddings_file='stored_embeddings.json', threshold=0.30, frame_skip=2, model_path=None):

        self.embeddings_file = embeddings_file
        self.threshold = threshold
        self.weak_threshold = 0.25
        self.frame_skip = frame_skip

        self.stored_embeddings = {}
        self.stored_embeddings_np = {}
        self.current_frame_count = 0

        self.lock = threading.Lock()
        # recent matches buffer for API/status
        self.recent_matches = []
        
        # Face tracking cache: {bbox_hash: {matched_person, last_seen_frame, embedding_hash}}
        # Prevents re-matching same face every frame
        self.face_cache = {}  # bbox_hash -> match data
        self.face_cache_timeout = 60  # frames to keep cached match (at frame_skip=2, ~2 seconds)
        self.cache_frame_count = 0  # Counter for cache expiry

        # -------- YOLO FACE DETECTOR --------
        try:
            # Use provided absolute model path if given, otherwise fallback to 'best.pt'
            model_to_load = model_path or os.path.join(os.path.dirname(__file__), 'best.pt')
            print(f"[YOLO] Loading model from: {model_to_load}")
            
            # Check if model file exists
            if not os.path.exists(model_to_load):
                raise FileNotFoundError(f"YOLO model file not found at: {model_to_load}")
            
            self.detector = YOLO(model_to_load)
            self.device = 'cpu'
            self.gpu_available = False

            try:
                import torch
                self.gpu_available = torch.cuda.is_available()
                self.device = 'cuda' if self.gpu_available else 'cpu'
                if self.gpu_available:
                    self.detector = self.detector.to(self.device)
                gpu_name = torch.cuda.get_device_name(0) if self.gpu_available else 'None'
                logging.info(f"[YOLO] Torch device: {self.device} | GPU Available: {self.gpu_available} | GPU Name: {gpu_name}")
            except Exception as e:
                self.device = 'cpu'
                self.gpu_available = False
                logging.warning(f"[YOLO] Torch GPU check error (non-critical): {e}")
            
            # Attempt to print minimal model info
            try:
                model_obj = getattr(self.detector, 'model', None)
                if model_obj is not None and hasattr(model_obj, 'names'):
                    logging.info(f"[YOLO] Model classes: {len(model_obj.names)}")
            except Exception:
                pass
            
            logging.info("[YOLO] Model loaded successfully ✓")
        except FileNotFoundError as e:
            logging.error(f"[ERROR] {e}")
            raise
        except Exception as e:
            logging.error(f"[ERROR] Failed to load YOLO model: {e}")
            raise

        # -------- ARCFACE RECOGNITION --------
        try:
            logging.info("[ArcFace] Loading InsightFace model...")
            providers = ['CUDAExecutionProvider','CPUExecutionProvider'] if self.gpu_available else ['CPUExecutionProvider']
            self.arcface = FaceAnalysis(name='buffalo_l', providers=providers)
            self.arcface.prepare(ctx_id=0 if self.gpu_available else -1, det_size=(640,640))
            
            # Check which provider is being used
            try:
                providers = self.arcface.providers
                gpu_enabled = 'CUDAExecutionProvider' in providers
                logging.info(f"[ArcFace] GPU Enabled: {gpu_enabled} | Providers: {providers}")
            except Exception:
                pass
            
            logging.info("[ArcFace] Model loaded successfully ✓")
        except Exception as e:
            logging.error(f"[ERROR] Failed to load ArcFace model: {e}")
            raise

        self.load_embeddings()

    # ---------------- LOAD DATABASE ----------------

    def load_embeddings(self):
        if os.path.exists(self.embeddings_file):
            with open(self.embeddings_file, 'r') as f:
                self.stored_embeddings = json.load(f)

            self.stored_embeddings_np = {}
            for name, data in self.stored_embeddings.items():
                emb = data.get('embedding')
                if emb:
                    self.stored_embeddings_np[name] = np.array(emb).reshape(1, -1)

            print(f"Loaded {len(self.stored_embeddings)} persons from database")

    def reload_embeddings(self):
        with self.lock:
            self.load_embeddings()

    # ---------------- YOLO FACE DETECTION ----------------

    def detect_faces(self, frame):

        faces = []
        # Lower confidence threshold for better detection (was 0.3)
        results = self.detector(frame, conf=0.6, verbose=False)

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes.xyxy:
                x1, y1, x2, y2 = map(int, box.tolist())

                face = frame[y1:y2, x1:x2]
                if face.size == 0:
                    continue

                faces.append({
                    "face": face,
                    "bbox": [x1, y1, x2-x1, y2-y1]
                })

        return faces

    # ---------------- ARCFACE EMBEDDING ----------------

    def get_embedding(self, face_img):

        try:
            faces = self.arcface.get(face_img)
            if len(faces) == 0:
                return None

            emb = faces[0].embedding
            emb = emb / np.linalg.norm(emb)   # normalize
            
            return emb

        except Exception as e:
            print(f"[ARCFACE ERROR] {e}")
            return None

    # ---------------- MATCHING ----------------

    def match_person(self, embedding):

        matches = []
        if not self.stored_embeddings_np:
            return matches

        emb = embedding.reshape(1, -1)
        best_candidate = None
        best_sim = -1.0

        for name, db_emb in self.stored_embeddings_np.items():
            sim = cosine_similarity(emb, db_emb)[0][0]

            if sim > best_sim:
                best_sim = sim
                best_candidate = name

            if sim >= self.threshold:
                matches.append({
                    "name": name,
                    "similarity": float(sim),
                    "confidence": f"{sim*100:.2f}%",
                    "strong_match": True
                })

        # If no strong match but top candidate surpasses weak threshold, keep as weak match
        if not matches and best_candidate is not None and best_sim >= self.weak_threshold:
            matches.append({
                "name": best_candidate,
                "similarity": float(best_sim),
                "confidence": f"{best_sim*100:.2f}%",
                "strong_match": False,
                "weak_match": True
            })
            logging.debug(f"[weak match] {best_candidate}: {best_sim*100:.2f}% (weak threshold {self.weak_threshold*100:.2f}%)")

        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches

    def get_recent_matches(self, limit=10):
        """Return recent matches (most recent first)"""
        return list(self.recent_matches[-limit:])[::-1]

    def add_recent_matches(self, matches, camera_name=None):
        """Add matches to a rolling recent_matches buffer with timestamp."""
        if not matches:
            return
        ts = tm.time()
        for m in matches:
            entry = {
                'name': m.get('name'),
                'similarity': m.get('similarity'),
                'confidence': m.get('confidence'),
                'timestamp': datetime.fromtimestamp(ts).isoformat(),
                'camera': camera_name
            }
            self.recent_matches.append(entry)
        # keep last 100 entries
        if len(self.recent_matches) > 100:
            self.recent_matches = self.recent_matches[-100:]

    def get_recent_matches(self, limit=5):
        """Return the most recent match entries up to `limit`."""
        return self.recent_matches[-limit:][::-1] if self.recent_matches else []

    # -------- FACE CACHE HELPERS --------
    
    def _bbox_hash(self, bbox):
        """Create hash of bbox for face tracking"""
        x, y, w, h = bbox
        # Quantize to 10-pixel grid to allow slight movement
        return (x // 10, y // 10, (w + 5) // 10, (h + 5) // 10)
    
    def _embedding_hash(self, embedding):
        """Create lightweight hash of embedding for caching"""
        if embedding is None:
            return None
        # Use first 5 values as a quick signature
        try:
            sig = tuple((embedding[:5] * 100).astype(int))
            return hash(sig)
        except:
            return None
    
    def _clean_face_cache(self):
        """Remove old entries from face cache"""
        self.cache_frame_count += 1
        if self.cache_frame_count % 30 == 0:  # Clean every 30 frames
            to_delete = [k for k, v in self.face_cache.items() 
                        if self.cache_frame_count - v.get('last_frame', 0) > self.face_cache_timeout]
            for k in to_delete:
                del self.face_cache[k]

    def _bbox_iou(self, bbox1, bbox2):
        """Return intersection-over-union for two bboxes."""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2

        xa1, ya1 = max(x1, x2), max(y1, y2)
        xa2, ya2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)

        inter_w = max(0, xa2 - xa1)
        inter_h = max(0, ya2 - ya1)
        if inter_w == 0 or inter_h == 0:
            return 0.0

        inter_area = inter_w * inter_h
        union_area = w1 * h1 + w2 * h2 - inter_area
        return inter_area / union_area if union_area > 0 else 0.0

    def _dedupe_boxes(self, boxes):
        """Remove duplicate/overlapping boxes, preferring matched boxes."""
        deduped = []
        for box in boxes:
            replaced = False
            for idx, existing in enumerate(deduped):
                if self._bbox_iou(box['bbox'], existing['bbox']) > 0.5:
                    # Keep matched box if either is matched
                    if box['has_match'] and not existing['has_match']:
                        deduped[idx] = box
                    replaced = True
                    break
            if not replaced:
                deduped.append(box)
        return deduped

    # ---------------- PROCESS FRAME ----------------

    def process_frame(self, frame):

        self.current_frame_count += 1

        if self.current_frame_count % self.frame_skip != 0:
            return {"faces_detected":0,"matches":[],"bounding_boxes":[]}
        
        # Clean expired face cache entries
        self._clean_face_cache()

        yolo_faces = self.detect_faces(frame)
        arcface_dets = self.arcface.get(frame)

        faces = []

        # Keep YOLO faces first (for overlay), then ArcFace detections for higher quality match
        for f in yolo_faces:
            faces.append({
                'face': f['face'],
                'bbox': f['bbox'],
                'source': 'yolo',
                'embedding': None
            })

        for af in arcface_dets:
            if not hasattr(af, 'bbox') or af.bbox is None:
                continue
            x1, y1, x2, y2 = map(int, af.bbox)
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                continue
            face_img = frame[y1:y2, x1:x2]
            if face_img.size == 0:
                continue

            emb = None
            if hasattr(af, 'embedding') and af.embedding is not None:
                emb = np.array(af.embedding)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                else:
                    emb = None

            faces.append({
                'face': face_img,
                'bbox': [x1, y1, x2 - x1, y2 - y1],
                'source': 'arcface',
                'embedding': emb
            })

        if len(yolo_faces) == 0 and len(arcface_dets) > 0:
            print(f"[FALLBACK] YOLO miss; using ArcFace detections: {len(arcface_dets)}" )

        bounding_boxes = []
        all_matches = []

        for face_data in faces:
            face = face_data['face']
            bbox = face_data['bbox']
            embedding = face_data.get('embedding')

            if embedding is None:
                embedding = self.get_embedding(face)

                if embedding is not None:
                    print(f"[INFO] Generated embedding from {face_data['source']} crop")

            if embedding is None:
                logging.debug(f"[DEBUG] No embedding from {face_data['source']} bbox {bbox}")
                matches = []
            else:
                matches = self.match_person(embedding)

            if matches:
                for m in matches:
                    m['bbox'] = bbox
                    all_matches.append(m)
                    self.recent_matches.append({
                        'name': m.get('name'),
                        'similarity': m.get('similarity'),
                        'confidence': m.get('confidence'),
                        'timestamp': datetime.now().isoformat(),
                        'camera': getattr(self, 'camera_name', None)
                    })
                if len(self.recent_matches) > 1000:
                    self.recent_matches = self.recent_matches[-1000:]

            bounding_boxes.append({
                'bbox': bbox,
                'has_match': len(matches) > 0,
                'matches': matches
            })

        bounding_boxes = self._dedupe_boxes(bounding_boxes)

        return {
            'faces_detected': len(faces),
            'matches': all_matches,
            'bounding_boxes': bounding_boxes
        }

    def get_recent_matches(self, limit=10):
        """Return recent matches (most recent first)"""
        return list(self.recent_matches[-limit:])[::-1]

    def add_recent_matches(self, matches, camera_name=None):
        """Add matches to a rolling recent_matches buffer with timestamp."""
        if not matches:
            return
        ts = tm.time()
        for m in matches:
            entry = {
                'name': m.get('name'),
                'similarity': m.get('similarity'),
                'confidence': m.get('confidence'),
                'timestamp': datetime.fromtimestamp(ts).isoformat(),
                'camera': camera_name
            }
            self.recent_matches.append(entry)
        # keep last 100 entries
        if len(self.recent_matches) > 100:
            self.recent_matches = self.recent_matches[-100:]

    def get_recent_matches(self, limit=5):
        """Return the most recent match entries up to `limit`."""
        return self.recent_matches[-limit:][::-1] if self.recent_matches else []


# ==============================
# VIDEO STREAM PROCESSOR
# ==============================

class VideoStreamProcessor:

    def __init__(self, detector):
        self.detector = detector
        self.cap = None
        self.is_processing = False
        self.current_source = 0
        self.camera_name = "camera"
        self.fps = 0.0
        self.last_frame_time = None
        self.health_status = "stopped"

    def open_camera(self, source=0, camera_name="camera"):

        self.current_source = source
        self.camera_name = camera_name

        if isinstance(source, str) and source.isdigit():
            source = int(source)

        # Windows webcam fix
        if sys.platform == "win32" and isinstance(source, int):
            # Try default backend first, fallback to DSHOW if needed
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                print(f"[CAMERA] Default backend failed, trying DSHOW...")
                self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise Exception("Cannot open camera")

        return True


    def process_stream(self, callback=None):

        self.is_processing = True
        self.health_status = "running"

        while self.is_processing:

            ret, frame = self.cap.read()

            if not ret:
                self.health_status = "no_frame"
                tm.sleep(0.05)
                continue

            # FPS calculation
            now = tm.time()
            if self.last_frame_time is not None:
                dt = now - self.last_frame_time
                if dt > 0:
                    self.fps = 1.0 / dt
            self.last_frame_time = now

            # detection
            result = self.detector.process_frame(frame)

            # draw boxes
            annotated = self.draw_boxes(frame.copy(), result["bounding_boxes"])

            if callback:
                callback(result, annotated)


    def draw_boxes(self, frame, boxes):

        if len(boxes) == 0:
            return frame

        for b in boxes:

            x, y, w, h = b["bbox"]
            
            # Ensure coordinates are valid
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                continue

            if b["has_match"]:
                color = (0, 0, 255)
                match = b["matches"][0]
                name = match.get("name", "Unknown")
                conf = match.get("confidence", "0.00%")
                label = f"{name} ({conf})"
            else:
                color = (0, 255, 0)
                label = "Unknown"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(frame, (x, y - 25), (x + w, y), color, -1)
            cv2.putText(frame, label, (x + 5, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame


    def stop(self):
        self.is_processing = False
        self.health_status = "stopped"
        if self.cap:
            self.cap.release()
            self.cap = None
