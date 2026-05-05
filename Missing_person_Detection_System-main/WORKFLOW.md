# Complete Workflow Guide

## How the System Works

### Step 1: Add Missing Person ✅

1. **Upload Image with Face**
   - Go to: http://localhost:5000/ (or use API)
   - Upload an image with a **clear, front-facing face**
   - Enter the person's name
   - Click submit

2. **System Processes Image**
   - System tries multiple face detection methods automatically
   - If face is detected, creates face embedding
   - Stores in database
   - **Person is now ready for detection!**

### Step 2: Start Live Detection 📹

1. **Start Camera Feed**
   - Go to: http://localhost:5000/realtime
   - Or send POST to `/api/stream/start` with:
     ```json
     {
       "source": 0,
       "camera_name": "Main Camera"
     }
     ```

2. **System Starts Monitoring**
   - Camera feed begins
   - System processes each frame
   - Detects all faces in the frame
   - Compares against stored persons

### Step 3: Automatic Detection & Alerts 🚨

When the missing person appears in the camera:

1. **Face Detected**
   - System detects face in live feed
   - Compares with stored embeddings
   - Calculates similarity score

2. **Match Found (≥65% confidence)**
   - ✅ **Snapshot automatically saved** to `snapshots/` folder
   - ✅ **Alert sent** via WebSocket
   - ✅ **Entry added** to alert history
   - ✅ **Visual indicator** on screen (red bounding box)

3. **You Get Notified**
   - Real-time alert appears
   - Snapshot available immediately
   - Can view in alert history

## Complete Example

```
1. Upload "John Doe" photo → ✅ Added to database
2. Start camera feed → 📹 Monitoring begins
3. John appears in camera → 🚨 ALERT! Snapshot saved!
4. View snapshot → 📸 See captured image
5. Check alert history → 📋 See all detections
```

## Important Notes

### ✅ After Uploading Person:
- Person is **immediately available** for detection
- No need to restart server
- Embeddings auto-reload

### ✅ During Live Detection:
- System detects **all faces** in frame
- Compares **each face** against database
- Works in **groups** (multiple people)
- **Fast detection** (< 1 second)

### ✅ When Match Found:
- **Automatic snapshot** saved
- **Alert notification** sent
- **Bounding box** shows on screen
- **Confidence score** displayed

## Troubleshooting

### "No face detected" when uploading?
- ✅ Use clear, front-facing photo
- ✅ Ensure good lighting
- ✅ Face should be clearly visible
- ✅ See `FACE_DETECTION_TIPS.md` for details

### Person not detected in live feed?
- ✅ Make sure person was successfully added
- ✅ Check camera is working
- ✅ Ensure face is clearly visible in camera
- ✅ Try lowering threshold (in code) if needed

### Camera not starting?
- ✅ Close other apps using camera
- ✅ Check http://localhost:5000/api/cameras
- ✅ Try different camera index (0, 1, 2)

## Quick Test

1. **Add yourself as missing person:**
   ```
   POST /target_person
   - name: "Test Person"
   - image: [your photo]
   ```

2. **Start detection:**
   ```
   POST /api/stream/start
   {"source": 0, "camera_name": "Test"}
   ```

3. **Look at camera:**
   - You should see yourself detected!
   - Alert will trigger
   - Snapshot will be saved

## API Flow

```
Upload Person → Store Embedding → Start Stream → Detect Faces → 
Match Found? → Save Snapshot → Send Alert → Log Event
```

Everything is **automatic** once you:
1. ✅ Upload the person
2. ✅ Start the camera feed

The system does the rest! 🚀
