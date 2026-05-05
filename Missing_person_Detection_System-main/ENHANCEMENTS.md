# Real-Time Missing Person Detection System - Enhancements

## Overview
This system has been enhanced for law enforcement use with real-time detection, multi-camera support, automatic snapshots, and comprehensive alerting.

## Key Features

### 1. **Enhanced Real-Time Detection**
- **Fast Multi-Face Detection**: Detects multiple faces in groups quickly
- **Optimized Performance**: Pre-computed embeddings for faster matching
- **Lower Detection Threshold**: Detects at 65% confidence for faster alerts
- **Better Frame Processing**: Processes every 3rd frame (configurable) for optimal speed
- **GPU Support Ready**: Architecture supports GPU acceleration

### 2. **Multi-Camera Support**
- **Webcam Support**: Standard USB/webcams (0, 1, 2, etc.)
- **RTSP Streams**: CCTV cameras via RTSP protocol
  - Format: `rtsp://username:password@ip:port/stream`
- **IP Cameras**: HTTP/HTTPS camera feeds
  - Format: `http://ip:port/video`
- **Video Files**: Support for video file processing
- **Camera Management**: API endpoints to list and manage cameras

### 3. **Automatic Snapshot Capture**
- **Instant Snapshots**: Automatically captures snapshots when a match is detected
- **Organized Storage**: Snapshots stored in `snapshots/` folder
- **Metadata**: Each snapshot includes timestamp, person name, and confidence
- **Annotated Images**: Snapshots include bounding boxes and labels
- **API Access**: Retrieve snapshots via `/api/snapshots/<filename>`

### 4. **Enhanced Alert System**
- **Multi-Channel Alerts**: 
  - WebSocket real-time alerts
  - Console logging
  - File-based alert history
- **Alert History**: Track all alerts with filtering capabilities
- **Smart Cooldown**: Prevents alert spam (5-minute cooldown per person per camera)
- **Alert Data Includes**:
  - Person name
  - Confidence score
  - Timestamp
  - Camera source
  - Snapshot path
  - Frame information

### 5. **Evidence Collection & Audit Logging**
- **Evidence API**: Retrieve all detection evidence with filtering
- **Audit Logging**: Complete audit trail for compliance
- **Date Filtering**: Filter evidence by date range
- **Person Filtering**: Filter by specific person
- **Compliance Ready**: Suitable for law enforcement evidence requirements

### 6. **Performance Optimizations**
- **Pre-computed Embeddings**: Faster matching using numpy arrays
- **Optimized Frame Skipping**: Configurable frame processing rate
- **Reduced Latency**: Minimal buffer sizes for RTSP streams
- **Better Error Handling**: Graceful failure recovery
- **Multi-threaded Processing**: Non-blocking stream processing

### 7. **Visual Enhancements**
- **Color-Coded Bounding Boxes**:
  - Red (bright): High confidence (≥80%)
  - Orange-Red: Medium-high (70-80%)
  - Yellow-Orange: Medium (65-70%)
  - Green: Detected but no match
- **Corner Markers**: Enhanced visibility in groups
- **Alert Indicators**: Visual "!" markers for high-confidence matches
- **Camera Overlay**: Shows camera name and frame count
- **Face Indexing**: Numbers faces in groups for easy identification

## API Endpoints

### Detection & Monitoring
- `POST /api/stream/start` - Start real-time detection
  - Body: `{"source": 0, "camera_name": "Main Camera"}`
- `POST /api/stream/stop` - Stop detection
- `GET /api/stream/status` - Get current status
- `POST /api/stream/reload` - Reload embeddings

### Alerts & Evidence
- `GET /api/alerts/history` - Get alert history
  - Query params: `limit`, `person_name`
- `GET /api/snapshots/<filename>` - Get snapshot image
- `GET /api/evidence` - Get evidence collection
  - Query params: `limit`, `person_name`, `start_date`, `end_date`

### Camera Management
- `GET /api/cameras` - List available cameras

### Audit & Compliance
- `GET /api/audit` - Get audit log
  - Query params: `limit`, `event_type`

### Person Management
- `POST /target_person` - Add missing person
- `GET /targets` - List all stored persons
- `POST /detect` - Detect person from image

## Usage Examples

### Starting Detection with Webcam
```bash
curl -X POST http://localhost:5000/api/stream/start \
  -H "Content-Type: application/json" \
  -d '{"source": 0, "camera_name": "Main Webcam"}'
```

### Starting Detection with RTSP Camera (CCTV)
```bash
curl -X POST http://localhost:5000/api/stream/start \
  -H "Content-Type: application/json" \
  -d '{
    "source": "rtsp://admin:password@192.168.1.100:554/stream1",
    "camera_name": "CCTV Entrance"
  }'
```

### Starting Detection with IP Camera
```bash
curl -X POST http://localhost:5000/api/stream/start \
  -H "Content-Type: application/json" \
  -d '{
    "source": "http://192.168.1.101:8080/video",
    "camera_name": "IP Camera 1"
  }'
```

### Getting Alert History
```bash
curl http://localhost:5000/api/alerts/history?limit=50
```

### Getting Evidence for Specific Person
```bash
curl "http://localhost:5000/api/evidence?person_name=John%20Doe&limit=100"
```

## Configuration

### Detection Threshold
- Default: 0.6 (60% similarity)
- Alert threshold: 0.65 (65% similarity) - triggers alerts
- High confidence: 0.7 (70% similarity) - strong alerts

### Frame Processing
- Frame skip: 3 (processes every 3rd frame)
- Adjustable in `RealTimeDetector` initialization

### Alert Cooldown
- Default: 300 seconds (5 minutes)
- Prevents duplicate alerts for same person on same camera

## File Structure
```
backend/
├── app.py                    # Main Flask application
├── realtime_detector.py      # Real-time detection engine
├── snapshots/                # Auto-captured snapshots
├── alerts/                   # Alert logs
├── evidence/                 # Evidence storage
├── uploads/                  # Uploaded images
└── audit.log                 # Audit trail

stored_embeddings.json        # Person database
```

## Law Enforcement Features

### 1. **Evidence Chain of Custody**
- All detections logged with timestamps
- Snapshots automatically saved
- Audit trail for all operations

### 2. **Multi-Camera Monitoring**
- Monitor multiple cameras simultaneously
- Support for various camera types
- Centralized management

### 3. **Real-Time Alerts**
- Instant notifications when matches found
- Visual and data alerts
- Historical tracking

### 4. **Compliance**
- Audit logging for all actions
- Evidence collection API
- Date and person filtering

## Performance Tips

1. **For Faster Detection**: Reduce `frame_skip` to 1 or 2 (more CPU intensive)
2. **For Better Accuracy**: Increase threshold to 0.7
3. **For Multiple Cameras**: Run multiple instances or use threading
4. **For RTSP Streams**: Ensure network bandwidth is adequate
5. **For GPU Acceleration**: Install CUDA-enabled TensorFlow

## Security Considerations

- Secure RTSP credentials
- Protect audit logs
- Encrypt sensitive data
- Use HTTPS in production
- Implement authentication for API endpoints

## Future Enhancements

- Email/SMS notifications (Twilio, SendGrid integration)
- Video recording of detection events
- Face tracking across frames
- Database integration for better storage
- Web dashboard for monitoring
- Mobile app for alerts
- Cloud storage integration
- Machine learning model fine-tuning

## Troubleshooting

### Camera Not Opening
- Check camera permissions
- Verify RTSP URL format
- Test camera with VLC or similar tool
- Check network connectivity for IP cameras

### Slow Detection
- Reduce frame resolution
- Increase frame_skip value
- Use GPU if available
- Reduce number of stored persons

### No Matches Found
- Check threshold value
- Verify embeddings are loaded
- Ensure face is clearly visible
- Check image quality

## Support

For issues or questions, check:
1. Logs in `alerts/alerts.log`
2. Audit trail in `audit.log`
3. Console output for real-time errors
