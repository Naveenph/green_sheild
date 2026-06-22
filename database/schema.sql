CREATE DATABASE IF NOT EXISTS greenshield_db;
USE greenshield_db;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plants Table (Information about different plants)
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    common_pests TEXT
);

-- Diseases Table (Information about plant diseases)
CREATE TABLE IF NOT EXISTS diseases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM('Fungal', 'Bacterial', 'Viral', 'Healthy') NOT NULL,
    symptoms TEXT,
    prevention TEXT,
    treatment TEXT,
    fertilizers TEXT,
    estimated_cost DECIMAL(10, 2),
    recovery_time VARCHAR(50)
);

-- Predictions Table (History of scans)
CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    disease_id INT,
    image_path VARCHAR(255),
    confidence FLOAT,
    severity ENUM('Mild', 'Moderate', 'Severe', 'N/A') DEFAULT 'N/A',
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (disease_id) REFERENCES diseases(id) ON DELETE SET NULL
);

-- Sample Data for Diseases
INSERT INTO diseases (name, category, symptoms, prevention, treatment, fertilizers, estimated_cost, recovery_time) VALUES
('Apple Scab', 'Fungal', 'Olive-green to black spots on leaves and fruit.', 'Remove fallen leaves, prune trees for better airflow.', 'Apply fungicides like Captan or Myclobutanil.', 'Potassium-rich fertilizers.', 45.00, '2-4 weeks'),
('Tomato Early Blight', 'Fungal', 'Brown spots with concentric rings on older leaves.', 'Rotate crops, avoid overhead watering.', 'Copper-based fungicides.', 'Balanced NPK 10-10-10.', 30.00, '1-3 weeks'),
('Potato Late Blight', 'Fungal', 'Dark, water-soaked spots on leaves and stems.', 'Plant resistant varieties, ensure proper spacing.', 'Mancozeb or Chlorothalonil fungicides.', 'Calcium-rich fertilizers.', 55.00, '3-5 weeks'),
('Healthy', 'Healthy', 'No signs of disease. Vibrant green leaves.', 'Maintain regular watering and fertilization.', 'N/A', 'Organic compost.', 0.00, 'N/A');
