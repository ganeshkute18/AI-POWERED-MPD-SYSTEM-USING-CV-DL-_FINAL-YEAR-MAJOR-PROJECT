# 🚨 AI-Powered Missing Person Detection System Using Computer Vision & Deep Learning

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv">
  <img src="https://img.shields.io/badge/YOLO-RealTime%20Detection-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/ArcFace-Face%20Recognition-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/DeepLearning-AI-purple?style=for-the-badge">
</p>

<p align="center">
  <b>Final Year Major Project</b><br>
  Real-Time Missing Person Detection using AI, CCTV Streams, Face Recognition, and Deep Learning.
</p>

---

# 📌 Project Overview

The **AI-Powered Missing Person Detection System** is an intelligent surveillance and identification platform designed to help authorities and organizations detect missing persons in real-time using:

* 🎥 CCTV / Webcam Streams
* 🧠 Deep Learning Models
* 👤 Face Recognition
* ⚡ Real-Time Alerts
* 📊 Live Monitoring Dashboard

The system combines **YOLO-based person detection** with **ArcFace facial embeddings** to identify registered missing persons from live video streams and uploaded images.

This project was developed as a **Final Year Major Project** for Computer Science Engineering (AI & Edge Computing). 

---

# ✨ Key Features

## 🔍 Face Registration System

* Register missing persons with image uploads
* Generate and store ArcFace embeddings
* Maintain searchable identity database

## 🎯 AI-Based Face Recognition

* Real-time face matching
* High-accuracy embedding comparison
* Multi-person detection support

## 📹 Live CCTV / Webcam Monitoring

* Start & stop realtime camera streams
* Webcam / RTSP / CCTV support
* Continuous AI surveillance

## 🚨 Smart Alert System

* Automatic detection alerts
* Snapshot evidence generation
* Alert logging system
* WebSocket notifications

## 🖥️ Interactive Dashboard

* Admin panel
* Realtime monitoring dashboard
* Camera management interface
* Detection analytics

## ☁️ Deployment Ready

* Docker support
* GPU acceleration support
* Cloud deployment compatible

---

# 🏗️ System Architecture

```text
Camera Feed / CCTV Stream
            ↓
      YOLO Detection
            ↓
      Face Extraction
            ↓
     ArcFace Embedding
            ↓
    Embedding Comparison
            ↓
     Match Verification
            ↓
   Alert + Snapshot + Log
            ↓
      Live Dashboard
```

---

# 🛠️ Tech Stack

| Technology            | Purpose             |
| --------------------- | ------------------- |
| Python                | Backend Development |
| Flask                 | API Server          |
| OpenCV                | Image Processing    |
| YOLO                  | Real-Time Detection |
| InsightFace / ArcFace | Face Recognition    |
| WebSocket             | Live Alerts         |
| HTML/CSS/JS           | Frontend            |
| Docker                | Containerization    |
| CUDA                  | GPU Acceleration    |

---

# 📂 Project Structure

```bash
Missing_person_Detection_System-main/
│
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
│
├── streams/
│   └── cameras.json
│
├── scripts/
│   ├── test_upload.py
│   └── test_enhanced_system.py
│
├── README.md
└── .gitignore
```



---

# ⚙️ Installation Guide

## 1️⃣ Clone Repository

```bash
git clone https://github.com/ganeshkute18/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

---

## 2️⃣ Create Conda Environment

```bash
conda create -n missing_person_detection python=3.10 -y
conda activate missing_person_detection
```

---

## 3️⃣ Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

# 🚀 GPU Setup (Recommended)

## CUDA Installation

```bash
conda install -c conda-forge cudatoolkit=12.1 cudnn -y
```

## Install CUDA-enabled PyTorch

```bash
conda install -c pytorch -c nvidia pytorch torchvision torchaudio pytorch-cuda=12.6 -y
```

## Install ONNX Runtime GPU

```bash
pip install onnxruntime-gpu==1.23.2
```



---

# ▶️ Running the Project

## Start Backend Server

```bash
cd backend
python app.py
```

---

# 🌐 Access Application

```text
http://localhost:5000
```

---

# 📡 API Endpoints

| Endpoint              | Method | Description              |
| --------------------- | ------ | ------------------------ |
| `/target_person`      | POST   | Register Missing Person  |
| `/targets`            | GET    | List Registered Persons  |
| `/detect`             | POST   | Detect Person from Image |
| `/api/stream/start`   | POST   | Start Camera Stream      |
| `/api/stream/stop`    | POST   | Stop Stream              |
| `/api/stream/status`  | GET    | Stream Status            |
| `/api/alerts/history` | GET    | Alert History            |
| `/health`             | GET    | Server Health            |



---

# 🖥️ Web Pages

| Route           | Description      |
| --------------- | ---------------- |
| `/`             | Landing Page     |
| `/camera`       | Camera Detection |
| `/realtime`     | Live Monitoring  |
| `/admin`        | Admin Dashboard  |
| `/instructions` | User Guide       |



---

# 📸 Screenshots

## 🏠 Dashboard

*Add dashboard screenshot here*

## 🎥 Live Detection

*Add realtime detection screenshot here*

## 👤 Admin Panel

*Add admin panel screenshot here*

## 🚨 Alert Detection

*Add alert snapshot here*

---

# 🧠 AI Models Used

## 🔹 YOLO

Used for:

* Person detection
* Real-time object tracking
* CCTV stream analysis

## 🔹 ArcFace (InsightFace)

Used for:

* Facial embeddings
* Face recognition
* Similarity matching

---

# 🐳 Docker Support

## Build Docker Image

```bash
docker build -t missing-person-detection:latest .
```

## Run Container

```bash
docker run -p 5000:5000 missing-person-detection:latest
```



---

# 📊 Future Enhancements

* 📡 Drone Feed Integration
* ☁️ Cloud Deployment
* 📱 Mobile App Support
* 🔔 SMS & Email Alerts
* 🛰️ GPS Tracking Integration
* 🤖 AI Analytics Dashboard
* 🧾 Automated Report Generation

---

# 🎯 Project Objectives

* Improve missing person identification speed
* Enable realtime surveillance monitoring
* Reduce manual searching efforts
* Support law enforcement investigations
* Enhance public safety using AI

---

# 👨‍💻 Developed By

## Ganesh Kute

B.Tech CSE (AI & Edge Computing)

Final Year Major Project

---

# 📜 License

This project is developed for educational and research purposes.

---

# ⭐ Support

If you found this project useful:

* 🌟 Star this repository
* 🍴 Fork the project
* 📢 Share with others

---

# 📬 Contact

## GitHub

GitHub

```text
https://github.com/ganeshkute18
```

---

# 🔥 Project Highlights

✅ Real-Time AI Detection
✅ Computer Vision Based
✅ Deep Learning Integrated
✅ CCTV Monitoring Support
✅ Alert & Evidence System
✅ Final Year Major Project
✅ Docker & GPU Ready
✅ Scalable Architecture

---

<p align="center">
  <b>🚀 AI + Computer Vision for Social Impact 🚀</b>
</p>
