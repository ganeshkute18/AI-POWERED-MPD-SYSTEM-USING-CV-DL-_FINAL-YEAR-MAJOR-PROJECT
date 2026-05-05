# Docker Quick Start Guide

## 🚀 Quick Start (Copy & Paste)

### 1. Build Image (from backend directory)
```powershell
cd backend
docker build -t missing-person-detector:gpu-v1.0 .
```

**Note**: This will automatically include `best.pt` and cuDNN 9 GPU support.

### 2. Run Container (with GPU & Volumes)
```powershell
docker run -d `
  --name missing-person-detector `
  --gpus all `
  -p 5001:5001 `
  -v "$(pwd)/uploads:/app/uploads" `
  -v "$(pwd)/snapshots:/app/snapshots" `
  -v "$(pwd)/evidence:/app/evidence" `
  -v "$(pwd)/alerts:/app/alerts" `
  -v "$(pwd)/stored_embeddings.json:/app/stored_embeddings.json" `
  missing-person-detector:gpu-v1.0
```

### 3. Check Logs (Verify GPU & Models Loaded)
```powershell
docker logs -f missing-person-detector
```

**Look for these lines**:
```
[YOLO] GPU Available: True | Device: NVIDIA GeForce RTX 3090 | Using: 0
[YOLO] Model loaded successfully ✓
[ArcFace] GPU Enabled: True | Providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
[ArcFace] Model loaded successfully ✓
```

### 4. Verify GPU is Working
```powershell
docker exec missing-person-detector python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

### 5. Access the Application
```powershell
# In your browser:
http://localhost:5001
```

### 6. Stop Container
```powershell
docker stop missing-person-detector
```

---

## 📋 What's Fixed

| Issue | Solution | Verification |
|-------|----------|--------------|
| best.pt missing | Auto-copied to container | `docker exec <container> ls -lh /app/best.pt` |
| ONNX GPU not working | Using cuDNN 9 base image | `docker exec <container> python -c "import onnxruntime; print(onnxruntime.get_available_providers())"` |
| No GPU logs | Added GPU detection & logging | Check startup logs for `[YOLO] GPU Available: True` |

---

## 📋 Key Files
|------|---------|
| `Dockerfile` | Production-ready Docker image definition |
| `requirements.txt` | Pinned Python dependencies (GPU-compatible) |
| `DOCKER_SETUP.md` | Comprehensive setup guide with all commands |
| `DOCKER_QUICK_START.md` | This file - quick reference |

---

## ⚡ Common Commands

### View GPU Status
```powershell
docker exec missing-person-detector nvidia-smi
```

### Check Dependencies
```powershell
docker exec missing-person-detector python -c "import torch; import ultralytics; import insightface; print('✓ All dependencies loaded')"
```

### Enter Container Shell
```powershell
docker exec -it missing-person-detector bash
```

### View Resource Usage
```powershell
docker stats missing-person-detector
```

### Restart Container
```powershell
docker restart missing-person-detector
```

---

## ⚠️ Troubleshooting

### Container exits immediately?
```powershell
docker logs missing-person-detector
```

### GPU not detected?
```powershell
# Verify NVIDIA Docker runtime
docker run --rm --gpus all ubuntu nvidia-smi

# Check if runtime is installed
docker info | findstr nvidia
```

### Port 5001 already in use?
```powershell
# Use different port (e.g., 5002)
docker run -d --name missing-person-detector --gpus all -p 5002:5001 ...
```

---

## 📝 Important Notes

✓ PyTorch 2.1.2 + CUDA 12.1 (GPU-enabled)  
✓ Python 3.10  
✓ All dependencies pinned for stability  
✓ OpenCV headless (no X11 needed)  
✓ GPU memory auto-managed  
✓ Health check enabled  

---

## 🔍 Detailed Documentation

For comprehensive setup guide with advanced options, see [DOCKER_SETUP.md](DOCKER_SETUP.md)
