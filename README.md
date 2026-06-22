# GreenShield – Smart Disease Detection for Plants

GreenShield is a full-stack AI-powered web application designed for early detection and management of plant diseases. This project serves as a comprehensive solution for farmers and agricultural enthusiasts to monitor crop health using state-of-the-art Deep Learning (CNN) and Computer Vision.

## 🚀 Features

- **AI Disease Detection**: Upload leaf images to detect diseases across multiple plant species (Tomato, Potato, Apple, Corn, etc.).
- **Smart Recommendations**: Get detailed treatment methods, suggested fertilizers, and prevention tips.
- **Farmer's Dashboard**: Track history, severity levels, and prediction confidence.
- **AI Chatbot**: A virtual farming assistant for real-time guidance.
- **Voice Assistant**: Hands-free interaction for results and advice.
- **PDF Reports**: Download professional diagnosis reports for record-keeping.
- **Admin Panel**: Manage disease data, view platform analytics, and user statistics.
- **Modern UI**: Fully responsive design with glassmorphism and dark/light mode.

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+), Chart.js, Font Awesome.
- **Backend**: Python Flask, Flask-SQLAlchemy, Flask-Login.
- **Database**: MySQL.
- **Machine Learning**: TensorFlow/Keras (CNN), OpenCV for image processing.
- **Tools**: NumPy, Pandas, Matplotlib, ReportLab.

## 📁 Project Structure

```text
green_shield/
├── main_server.py      # Flask Application Entry Point
├── config.py           # Configuration & Environment Settings
├── database/           # SQL Schema & Migration Scripts
├── models/             # ML Model Architecture & Logic
├── scripts/            # Database Setup & Training Scripts
├── static/             # Assets (CSS, JS, Images)
├── templates/          # HTML Templates (Jinja2)
├── requirements.txt    # Python Dependencies
└── README.md           # Project Documentation
```

## ⚙️ Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd green_shield
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Configuration**
   - Start Apache and MySQL in your XAMPP Control Panel.
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - (Optional) Open `.env` and adjust the `DATABASE_URL` if your MySQL port is not default `3306` or has a root password.
   - Run the setup script to automatically create and seed the database:
     ```bash
     python scripts/setup_db.py
     ```

4. **Run the Application**
   ```bash
   python main_server.py
   ```
   Access the app at `http://127.0.0.1:8000`.

## 🧠 Machine Learning Model

The system uses a **Convolutional Neural Network (CNN)** trained on the **PlantVillage dataset**. 
- **Input Size**: 224x224 RGB.
- **Preprocessing**: Gaussian Blur, Normalization.
- **Layers**: 3 Conv blocks with Max Pooling, followed by a Dense layer with Dropout.
- **Accuracy**: ~96% on validation data.

## 👨‍💻 Project Developed By
**[Your Name]** - Final Year Engineering Project

---
*GreenShield - Empowering Agriculture through Technology.*
