# GPU Docker Setup Guide

## Prerequisites

### 1. NVIDIA GPU Requirements
- NVIDIA GPU with CUDA support (GTX 10xx, RTX 20xx/30xx/40xx series or newer)
- At least 4GB VRAM recommended
- Latest NVIDIA drivers installed

### 2. NVIDIA Docker Support
Install NVIDIA Container Toolkit:

**Windows:**
```powershell
# Download and install NVIDIA Docker Desktop extension
# Or use Docker Desktop with WSL2 + NVIDIA drivers
```

**Linux:**
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA Docker
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 3. Verify GPU Access
```bash
# Check NVIDIA drivers
nvidia-smi

# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi
```

---

## Build and Run with GPU

### Option 1: Docker Compose (Recommended)
```bash
cd backend

# Build and run with GPU support
docker-compose up --build
```

### Option 2: Docker Run
```bash
cd backend

# Build the image
docker build -t missing-person-gpu .

# Run with GPU access
docker run --rm --gpus all -p 5001:5001 \
  -v "$(pwd)/uploads:/app/uploads" \
  -v "$(pwd)/snapshots:/app/snapshots" \
  -v "$(pwd)/alerts:/app/alerts" \
  missing-person-gpu
```

---

## Performance Comparison

| Component | CPU Only | GPU Enabled | Improvement |
|-----------|----------|-------------|-------------|
| YOLO Detection | ~50-100ms | ~10-20ms | 5-10x faster |
| Face Embedding | ~200-500ms | ~20-50ms | 10x faster |
| Total FPS | 2-5 FPS | 15-30 FPS | 6-10x faster |
| Memory Usage | 2-4GB RAM | 4-8GB VRAM | Higher but faster |

---

## Troubleshooting

### GPU Not Detected
```bash
# Check if GPU is available in container
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi

# Check PyTorch GPU detection
docker run --rm --gpus all missing-person-gpu python -c "import torch; print(torch.cuda.is_available())"
```

### CUDA Version Mismatch
If you get CUDA version errors:
1. Update NVIDIA drivers to latest
2. Use a different CUDA version in Dockerfile (11.6, 11.7, 12.1, etc.)
3. Check GPU compatibility: https://developer.nvidia.com/cuda-gpus

### Memory Issues
- Reduce batch size in processing
- Use smaller YOLO model
- Add `--memory=8g` to docker run

---

## Configuration

### Environment Variables
```bash
# Force GPU usage
export CUDA_VISIBLE_DEVICES=0

# Limit GPU memory usage
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Model Selection
For lower-end GPUs, consider:
- YOLOv8n (nano) instead of default model
- Lower confidence thresholds
- Smaller input image sizes

---

## Monitoring GPU Usage

```bash
# Monitor GPU usage in real-time
watch -n 1 nvidia-smi

# Check GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

---

## Fallback to CPU

If GPU setup fails, the container will automatically fall back to CPU processing. No code changes needed!