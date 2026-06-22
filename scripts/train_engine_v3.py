import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import os
import numpy as np
import cv2
import matplotlib.pyplot as plt

# Dataset Configuration (Updated for Kaggle Structure)
DATASET_DIR = 'data/plantvillage/tomato/train'
MODEL_SAVE_PATH = 'models/plant_disease_model.h5'
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10 

def build_model(num_classes):
    print("Building Neural Network using MobileNetV2 Transfer Learning...")
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Freeze the base layers to speed up training
    for layer in base_model.layers:
        layer.trainable = False
        
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def start_training():
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory {DATASET_DIR} not found.")
        return

    # Data Augmentation & Loading
    datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )

    train_gen = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training'
    )

    val_gen = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation'
    )

    num_classes = train_gen.num_classes
    model = build_model(num_classes)
    
    print(f"Training on {num_classes} classes...")
    history = model.fit(
        train_gen,
        epochs=EPOCHS,
        validation_data=val_gen
    )

    # Ensure models directory exists
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    
    # Save the model
    model.save(MODEL_SAVE_PATH)
    print(f"\nTRAINING COMPLETE!")
    print(f"Model saved to: {MODEL_SAVE_PATH}")
    
    # Save class names to a text file for the backend to use
    class_indices = train_gen.class_indices
    class_names = list(class_indices.keys())
    with open('models/classes.txt', 'w') as f:
        for name in class_names:
            f.write(f"{name}\n")
    
    print(f"Class Mapping saved to models/classes.txt")
    
    return history

if __name__ == '__main__':
    start_training()
