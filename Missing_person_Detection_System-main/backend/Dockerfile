FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}:/usr/local/cuda/lib64/stubs \
    MODEL_PATH=/app/best.pt

WORKDIR /app

# ============================================================================
# 1. Install System Dependencies
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# ============================================================================
# 2. Upgrade pip, setuptools, and wheel (Critical for dependency resolution)
# ============================================================================
RUN pip install --upgrade pip setuptools wheel

# ============================================================================
# 3. Install PyTorch with CUDA 12.1 Support (MUST be before other packages)
# ============================================================================
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    torchvision==0.16.2 \
    torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121

# ============================================================================
# 3b. Verify cuDNN and CUDA libraries are available
# ============================================================================
RUN ldconfig -p | grep -E 'libcudnn|libcublas' || echo 'Warning: CUDA/cuDNN libs check'

# ============================================================================
# 4. Install Project Dependencies (Pre-compiled binaries where possible)
# ============================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt 2>&1 | grep -v "already satisfied" || true

# ============================================================================
# 5. Verify GPU Setup (Optional - for debugging)
# ============================================================================
RUN python -c "import torch; print(f'PyTorch Version: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# ============================================================================
# 6. Copy Application Files
# ============================================================================
COPY app.py realtime_detector.py ./
COPY best.pt ./
COPY templates/ templates/
COPY static/ static/

# ============================================================================
# 7. Create Required Directories
# ============================================================================
RUN mkdir -p uploads snapshots alerts evidence

# ============================================================================
# 8. Expose Port
# ============================================================================
EXPOSE 5001

# ============================================================================
# 9. Health Check
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# ============================================================================
# 10. Run Application
# ============================================================================
CMD ["python", "app.py"]
