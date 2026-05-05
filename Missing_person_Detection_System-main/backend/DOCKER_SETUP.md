# Production Docker Setup Guide

## Overview
This guide provides production-ready Docker setup for the Missing Person Detection System with GPU support.

---

## ✅ What's Fixed in This Setup

### 1. YOLO Model (best.pt) ✓
- **Issue**: Model file missing in container
- **Fix**: Dockerfile now copies `best.pt` automatically
- **Location**: `/app/best.pt` inside container
- **Auto-detection**: If model missing, clear error message printed at startup

### 2. ONNX GPU Support (cuDNN 9) ✓
- **Issue**: InsightFace GPU failed (libcudnn.so.9 not found)
- **Fix**: Using `nvidia/cuda:12.1.0-cudnn9-runtime-ubuntu22.04` base image
- **Result**: ONNX Runtime GPU provider automatically enabled
- **Verification**: Check logs at startup for GPU provider status

### 3. GPU Auto-Detection ✓
- **PyTorch GPU**: Automatically detected and logged at startup
- **ONNX GPU**: Providers logged at startup
- **Example output**:
  ```
  [YOLO] GPU Available: True | Device: NVIDIA GeForce RTX 3090 | Using: 0
  [ArcFace] GPU Enabled: True | Providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
  ```

---

## Prerequisites

- **Docker**: 24.0+
- **NVIDIA Docker Runtime**: Installed and configured
- **NVIDIA GPU**: With CUDA 12.1 support
- **Available disk space**: ~10-15GB for image build

### Verify NVIDIA Docker Setup

```powershell
# Check if nvidia-docker is available
docker run --rm --gpus all ubuntu nvidia-smi

# Output should show GPU info if properly configured
```

---

## 1. Build the Docker Image

### Standard Build (with build cache)
```powershell
cd backend
docker build -t missing-person-detector:gpu-v1.0 .
```

### Build with No Cache (force rebuild all layers)
```powershell
docker build --no-cache -t missing-person-detector:gpu-v1.0 .
```

### Build with Progress Output
```powershell
docker build -t missing-person-detector:gpu-v1.0 --progress=plain .
```

---

## 2. Run the Docker Container

### Basic Run (with GPU support)
```powershell
docker run -d `
  --name missing-person-detector `
  --gpus all `
  -p 5001:5001 `
  -v "$(pwd)/uploads:/app/uploads" `
  -v "$(pwd)/snapshots:/app/snapshots" `
  -v "$(pwd)/evidence:/app/evidence" `
  -v "$(pwd)/alerts:/app/alerts" `
  missing-person-detector:gpu-v1.0
```

### Run with Environment Variables
```powershell
docker run -d `
  --name missing-person-detector `
  --gpus all `
  -p 5001:5001 `
  -e FLASK_ENV=production `
  -e DEBUG=False `
  -v "$(pwd)/uploads:/app/uploads" `
  -v "$(pwd)/snapshots:/app/snapshots" `
  -v "$(pwd)/evidence:/app/evidence" `
  -v "$(pwd)/alerts:/app/alerts" `
  missing-person-detector:gpu-v1.0
```

### Run with GPU Device Specification
```powershell
# Run on GPU 0 only
docker run -d `
  --name missing-person-detector `
  --gpus device=0 `
  -p 5001:5001 `
  -v "$(pwd)/uploads:/app/uploads" `
  -v "$(pwd)/snapshots:/app/snapshots" `
  -v "$(pwd)/evidence:/app/evidence" `
  -v "$(pwd)/alerts:/app/alerts" `
  missing-person-detector:gpu-v1.0
```

### Run in Interactive Mode (for debugging)
```powershell
docker run -it `
  --gpus all `
  -p 5001:5001 `
  -v "$(pwd)/uploads:/app/uploads" `
  -v "$(pwd)/snapshots:/app/snapshots" `
  -v "$(pwd)/evidence:/app/evidence" `
  -v "$(pwd)/alerts:/app/alerts" `
  missing-person-detector:gpu-v1.0 `
  bash
```

---

## 3. Verify GPU is Working Inside Container

### Check GPU Availability
```powershell
docker exec missing-person-detector python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU Count: {torch.cuda.device_count()}')"
```

### Full GPU Diagnostic
```powershell
docker exec missing-person-detector python -c "
import torch
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'CUDA Device Count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'Current GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')
"
```

### Check NVIDIA GPU Info
```powershell
docker exec missing-person-detector nvidia-smi
```

---

## 4. Verify Dependencies Are Installed

### Check PyTorch with CUDA
```powershell
docker exec missing-person-detector python -c "
import torch
import torchvision
import torchaudio
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ TorchVision: {torchvision.__version__}')
print(f'✓ TorchAudio: {torchaudio.__version__}')
"
```

### Check All Core Libraries
```powershell
docker exec missing-person-detector python -c "
import numpy as np
import cv2
import flask
import ultralytics
import insightface
import onnxruntime as ort
print(f'✓ NumPy: {np.__version__}')
print(f'✓ OpenCV: {cv2.__version__}')
print(f'✓ Flask: {flask.__version__}')
print(f'✓ Ultralytics: {ultralytics.__version__}')
print(f'✓ InsightFace: {insightface.__version__}')
print(f'✓ ONNX Runtime: {ort.__version__}')
print(f'✓ ONNX Runtime GPU Available: {ort.get_available_providers()}')
"
```

---

## 5. View Container Logs

### Real-time Logs
```powershell
docker logs -f missing-person-detector
```

### Last 100 Lines
```powershell
docker logs --tail 100 missing-person-detector
```

### With Timestamps
```powershell
docker logs -f --timestamps missing-person-detector
```

---

## 6. Container Management Commands

### Stop Container
```powershell
docker stop missing-person-detector
```

### Start Container
```powershell
docker start missing-person-detector
```

### Restart Container
```powershell
docker restart missing-person-detector
```

### Remove Container
```powershell
docker rm missing-person-detector
```

### Access Container Shell
```powershell
docker exec -it missing-person-detector bash
```

### View Container Info
```powershell
docker inspect missing-person-detector
```

### View Resource Usage
```powershell
docker stats missing-person-detector
```

---

## 7. Verify GPU & Model Setup ✓

### Verify YOLO Model is Present
```powershell
docker exec missing-person-detector ls -lh /app/best.pt
```

**Expected output**: File size ~100-500MB (depending on model)

### Verify YOLO GPU Detection
```powershell
docker exec missing-person-detector python -c "from ultralytics import YOLO; import torch; print(f'PyTorch GPU: {torch.cuda.is_available()}'); model = YOLO('/app/best.pt'); print(f'YOLO Device: {model.device}')"
```

**Expected**: `PyTorch GPU: True` and YOLO device shows GPU ID (0, 1, etc.)

### Verify ONNX GPU Provider
```powershell
docker exec missing-person-detector python -c "import onnxruntime; providers = onnxruntime.get_available_providers(); print(f'ONNX Providers: {providers}'); print(f'GPU Enabled: {\"CUDAExecutionProvider\" in providers}')"
```

**Expected**: `GPU Enabled: True` and `CUDAExecutionProvider` in list

### Verify InsightFace GPU
```powershell
docker exec missing-person-detector python -c "from insightface.app import FaceAnalysis; face_analysis = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider','CPUExecutionProvider']); face_analysis.prepare(ctx_id=0); print(f'Providers: {face_analysis.providers}')"
```

**Expected**: `CUDAExecutionProvider` in providers list

### Check Application Startup Logs
```powershell
docker logs missing-person-detector | findstr "YOLO\|ArcFace\|GPU"
```

**Expected output** (first 5 seconds):
```
[YOLO] Loading model from: /app/best.pt
[YOLO] GPU Available: True | Device: NVIDIA GeForce RTX 3090 | Using: 0
[YOLO] Model loaded successfully ✓
[ArcFace] Loading InsightFace model...
[ArcFace] GPU Enabled: True | Providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
[ArcFace] Model loaded successfully ✓
```

---

## 8. Image Management

### List Images
```powershell
docker images | findstr missing-person-detector
```

### Remove Image
```powershell
docker rmi missing-person-detector:gpu-v1.0
```

### Push to Registry (Optional)
```powershell
docker tag missing-person-detector:gpu-v1.0 <registry>/<repository>:<tag>
docker push <registry>/<repository>:<tag>
```

---

## 9. Troubleshooting

### Issue: Container exits immediately
```powershell
# Check logs
docker logs missing-person-detector

# Run with interactive bash to debug
docker run -it --gpus all missing-person-detector:gpu-v1.0 bash
```

### Issue: GPU not detected in container
```powershell
# Verify NVIDIA runtime
docker run --rm --gpus all ubuntu nvidia-smi

# Check if runtime is installed
docker info | findstr nvidia
```

### Issue: Out of memory during build
```powershell
# Try building with limited resources
docker build --memory 8g -t missing-person-detector:gpu-v1.0 .
```

### Issue: Dependency conflicts
```powershell
# Rebuild without cache
docker build --no-cache -t missing-person-detector:gpu-v1.0 .

# Or run with verbose pip output
docker run -it --gpus all missing-person-detector:gpu-v1.0 bash
pip install -v -r requirements.txt
```

---

## 10. Production Deployment Checklist

- [ ] Image built successfully
- [ ] GPU is detected inside container
- [ ] All dependencies verified
- [ ] Port 5001 is accessible
- [ ] Volume mounts are correct
- [ ] Health check passes
- [ ] Logs show Flask app started on 0.0.0.0:5001
- [ ] Test API endpoints from host machine
- [ ] Monitor resource usage during operation

---

## 11. Docker Compose (Optional)

Create `docker-compose.yml` for easier orchestration:

```yaml
version: '3.8'

services:
  missing-person-detector:
    build:
      context: .
      dockerfile: Dockerfile
    image: missing-person-detector:gpu-v1.0
    container_name: missing-person-detector
    ports:
      - "5001:5001"
    volumes:
      - ./uploads:/app/uploads
      - ./snapshots:/app/snapshots
      - ./evidence:/app/evidence
      - ./alerts:/app/alerts
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Run with Docker Compose
```powershell
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## Notes

- **Image Size**: ~4-5GB (expected for GPU ML workloads)
- **Build Time**: 10-15 minutes (depends on network and system)
- **GPU Memory**: Allocate based on your model requirements
- **Python 3.10**: Compatible with all specified packages
- **CUDA 12.1**: Required for PyTorch and TensorRT compatibility
