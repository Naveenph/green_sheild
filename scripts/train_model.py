import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from models.cnn_model import PlantDiseaseModel
import matplotlib.pyplot as plt
import os

def train():
    # Dataset path (Download PlantVillage and place it here)
    dataset_path = 'data/plantvillage'
    
    if not os.path.exists(dataset_path):
        print("Dataset not found. Please download PlantVillage and place it in 'data/plantvillage'.")
        return

    # Data Augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )

    train_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='training'
    )

    validation_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='validation'
    )

    # Build model from our architecture
    pm = PlantDiseaseModel()
    model = pm.model

    # Train
    history = model.fit(
        train_generator,
        epochs=10,
        validation_data=validation_generator
    )

    # Save model
    model.save('models/plant_model.h5')
    print("Model trained and saved to models/plant_model.h5")

    # Plot Accuracy
    plt.plot(history.history['accuracy'], label='accuracy')
    plt.plot(history.history['val_accuracy'], label = 'val_accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.ylim([0, 1])
    plt.legend(loc='lower right')
    plt.savefig('static/images/accuracy_graph.png')

if __name__ == '__main__':
    train()
