import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.cnn_model import PlantDiseaseModel

# Create a dummy image for testing if none exists
test_img = 'test_specimen.jpg'
import cv2
import numpy as np
dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
cv2.imwrite(test_img, dummy_img)

try:
    model = PlantDiseaseModel()
    print("Model initialized")
    disease, confidence = model.predict(test_img)
    print(f"Prediction: {disease} ({confidence})")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(test_img):
        os.remove(test_img)
