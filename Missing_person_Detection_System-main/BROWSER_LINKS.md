# 🌐 Direct Browser Links

## Main Application Links

Once your server is running on `http://localhost:5000`, use these direct links:

### 🏠 Home Page
**http://localhost:5000/**

### 📹 Real-Time Detection Dashboard
**http://localhost:5000/realtime**

### 📷 Camera Detection Page
**http://localhost:5000/camera**

---

## API Endpoints (for testing)

### Health Check
**http://localhost:5000/health**

### List Available Cameras
**http://localhost:5000/api/cameras**

### Stream Status
**http://localhost:5000/api/stream/status**

### Alert History
**http://localhost:5000/api/alerts/history**

### Evidence Collection
**http://localhost:5000/api/evidence**

### Audit Log
**http://localhost:5000/api/audit**

---

## Quick Start Steps

1. **Start the server:**
   ```bash
   cd backend
   python app.py
   ```

2. **Open in browser:**
   - Main page: http://localhost:5000/
   - Real-time detection: http://localhost:5000/realtime

3. **Check available cameras:**
   - Visit: http://localhost:5000/api/cameras

4. **Start detection:**
   - Use the web interface or send POST request to `/api/stream/start`

---

## Troubleshooting Camera Issues

If camera is not starting:

1. **Check if camera is available:**
   - Visit: http://localhost:5000/api/cameras
   - This will show which cameras are detected

2. **Test camera:**
   - Send POST to `/api/cameras/test` with `{"source": 0}`

3. **Common fixes:**
   - Close other applications using the camera (Zoom, Teams, etc.)
   - Try different camera index (0, 1, 2, etc.)
   - Restart the server
   - Check camera permissions in Windows settings

4. **For Windows:**
   - The system now uses DirectShow backend for better compatibility
   - Make sure no other app is using the camera

---

## Example: Starting Detection via Browser Console

Open browser console (F12) on the realtime page and run:

```javascript
fetch('http://localhost:5000/api/stream/start', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({source: 0, camera_name: 'Webcam'})
})
.then(r => r.json())
.then(data => console.log(data));
```

---

**Note:** Make sure the Flask server is running before opening these links!
