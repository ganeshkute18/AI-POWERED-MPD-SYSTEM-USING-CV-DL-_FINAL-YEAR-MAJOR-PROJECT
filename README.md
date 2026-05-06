Missing Person Detection System

A Flask-based missing person detection API with real-time camera streaming, missing person registration, alerting, and snapshot capture.

This project uses ArcFace embeddings from InsightFace for face registration and matching, and a YOLO-based realtime detector for live camera streams.

Features

Register Missing Person: Upload a person's face image and store normalized ArcFace embeddings.

List Stored Targets: Retrieve all registered missing persons and metadata.

Single Image Detection: Detect and match a face from an uploaded image.

Realtime Stream Detection: Start and stop webcam/RTSP/CCTV streams for live matching.

Live Dashboard: Web pages for admin, camera view, realtime monitoring, and instructions.

Alert System: Save alert snapshots, log alerts, and emit WebSocket notifications.

Camera Configuration: Manage configured cameras in streams/cameras.json.

Project Structure

Missing_person_Detection_System-main/
├── backend/
│   ├── app.py
│   ├── realtime_detector.py
│   ├── requirements.txt
│   ├── best.pt
│   ├── stored_embeddings.json
│   ├── uploads/
│   ├── snapshots/
│   ├── alerts/
│   ├── evidence/
│   ├── static/
│   └── templates/
├── streams/
│   └── cameras.json
├── scripts/
│   ├── test_upload.py
│   └── test_enhanced_system.py
├── README.md
└── .gitignore

Installation

The recommended setup is a Conda environment, because it is safer for managing CUDA and GPU dependencies.

Create and activate a Conda environment:

conda create -n missing_person_detection python=3.10 -y
conda activate missing_person_detection

Install the core backend requirements inside the Conda environment:

cd backend
pip install -r requirements.txt

Install GPU-specific runtime packages after the base requirements:

conda install -c conda-forge cudatoolkit=12.1 cudnn -y
# On Windows, install a CUDA-enabled PyTorch build from the PyTorch/NVIDIA channels.
conda install -c pytorch -c nvidia pytorch torchvision torchaudio pytorch-cuda=12.6 -y
pip install onnxruntime-gpu==1.23.2

If you prefer pip for PyTorch, use the official PyTorch CUDA index instead:

pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
pip install onnxruntime-gpu==1.23.2

Why this order matters

Install requirements.txt first in the Conda environment so the base Python dependencies are satisfied.

Then install GPU runtime packages, which are platform-specific and best managed by Conda.

This avoids mixing incompatible CPU and GPU builds.

CPU vs GPU

The project works on CPU, but GPU acceleration is strongly recommended for better realtime performance.

insightface is configured to prefer CUDAExecutionProvider and fall back to CPU if GPU is unavailable.

ultralytics will also run faster with a CUDA-enabled PyTorch installation.

Running the API

Start the Flask server:

cd backend
python app.py

Open the UI or access the API at:

http://localhost:5000

Main API Endpoints

Register a Missing Person

POST /target_person

Request:

name: string

image: file upload

Response:

success: true/false

message: status message

name: registered person name

total_persons: current database size

List Registered Targets

GET /targets

Response contains:

success

count

targets array of stored persons

Delete a Registered Person

DELETE /target_person/<name>

Removes a stored person by name.

Detect Person from Image

POST /detect

Request:

image: file upload

Response returns matching persons if found.

Health Check

GET /health

Returns API status.

Start Realtime Stream

POST /api/stream/start

Request body JSON:

source: webcam index or stream URL

camera_name: optional camera label

Stop Realtime Stream

POST /api/stream/stop

Stream Status

GET /api/stream/status

Reload Embeddings

POST /api/stream/reload

Alert History

GET /api/alerts/history

Optional query params:

limit

person_name

Snapshot Access

GET /api/snapshots/<filename>

Camera Management

GET /api/camerasPOST /api/cameras/save

Web Interface

The server also serves frontend pages at:

/ — main landing page

/camera — camera detection page

/realtime — realtime dashboard

/admin — admin panel

/instructions — usage instructions

Supported Image Formats

PNG

JPG/JPEG

GIF

BMP

Maximum upload size: 16MB

Notes

Face registration uses InsightFace / ArcFace for embeddings.

Realtime detection uses a YOLO model stored as backend/best.pt.

Stored embeddings are kept in backend/stored_embeddings.json.

Uploaded images are stored temporarily in backend/uploads/.

Alert snapshots are saved in backend/snapshots/.

Logs are written under backend/alerts/alerts.log.

Camera sources are defined in streams/cameras.json.

Using the Test Scripts

If you want to test the API with scripts, run them from the project root:

python scripts/test_upload.py <image_path> "Name"
python scripts/test_enhanced_system.py

Docker / Containerization

What is Dockerization?

Dockerization packages your entire application (Python interpreter, dependencies, system libraries, code) into a lightweight container. Benefits include:

Consistency: Works the same on any machine with Docker installed

Isolation: Keeps your app and dependencies isolated from the host system

Portability: Deploy to any cloud provider, server, or local environment

Easy deployment: One command to run the entire app

Prerequisites

Install Docker: https://docs.docker.com/get-docker/

Verify installation:

docker --version

How to Build and Run

Build the Docker image:

cd backend
docker build -t missing-person-detection:latest .

This command reads the Dockerfile, installs dependencies from requirements.txt, and creates a reusable image.

Run a container from the image:

docker run -p 5000:5000 missing-person-detection:latest

This starts a container and maps port 5000 (container) to port 5000 (host machine).

Access the app:Open http://localhost:5000 in your browser.

Docker and File Persistence

By default, files created inside a container (uploads, snapshots, embeddings) are lost when the container stops.

To persist data, mount a local folder:

docker run -p 5000:5000 \
  -v $(pwd)/backend/uploads:/app/uploads \
  -v $(pwd)/backend/snapshots:/app/snapshots \
  -v $(pwd)/backend/stored_embeddings.json:/app/stored_embeddings.json \
  missing-person-detection:latest

This command maps local folders to container paths so data persists on your host machine.

Docker and GPU Support

GPU support inside Docker requires additional setup:

Install NVIDIA Docker runtime:

# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2

Use a CUDA-enabled base image. Edit backend/Dockerfile:

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 libxcb1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]

Run with GPU enabled:

docker run --gpus all -p 5000:5000 missing-person-detection:latest

Understanding the Files

Dockerfile: Defines how to build the image (base OS, dependencies, how to start the app)

.dockerignore: Tells Docker what NOT to copy into the image (keeps image size small):

venv/ — local virtual environments

__pycache__/ — Python cache

.git/ — Git metadata

.env — local environment files

Common Docker Commands

# Build image
docker build -t missing-person-detection:latest .

# List images
docker images

# Run container (foreground)
docker run -p 5000:5000 missing-person-detection:latest

# Run container (background)
docker run -d -p 5000:5000 missing-person-detection:latest

# List running containers
docker ps

# Stop a container
docker stop <container_id>

# Remove a stopped container
docker rm <container_id>

# View container logs
docker logs <container_id>

# Enter a running container shell
docker exec -it <container_id> /bin/bash

# Remove unused images
docker image prune

Troubleshooting

Issue: Container exits immediately.

Check logs: docker logs <container_id>

Ensure backend/requirements.txt and app.py are correct

Issue: Port already in use.

Use a different port: docker run -p 8000:5000 missing-person-detection:latest

Then access http://localhost:8000

Issue: GPU not recognized inside container.

Verify NVIDIA Docker is installed: docker run --rm --gpus all nvidia/cuda:12.1.0-runtime nvidia-smi

Ensure your GPU drivers are up to date on the host
