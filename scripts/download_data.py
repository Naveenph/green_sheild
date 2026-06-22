import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def download_kaggle_dataset():
    username = os.getenv('KAGGLE_USERNAME')
    key = os.getenv('KAGGLE_KEY')
    
    if not username or not key:
        print("ERROR: KAGGLE_USERNAME or KAGGLE_KEY not found in .env file.")
        print("Please add them to your .env file to continue.")
        return

    # Set environment variables for the Kaggle API
    os.environ['KAGGLE_USERNAME'] = username
    os.environ['KAGGLE_KEY'] = key

    try:
        import kaggle
        print("Initializing Kaggle Download...")
        
        # Dataset identifier (Corrected to kaustubhb999)
        dataset = "kaustubhb999/tomatoleaf"
        path = "data/plantvillage"
        
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Download and unzip
        kaggle.api.dataset_download_files(dataset, path=path, unzip=True)
        
        print(f"SUCCESS: Dataset downloaded and extracted to {path}")
        print("You can now run 'python scripts/train_engine_v3.py' to start training.")
        
    except Exception as e:
        print(f"Error during download: {e}")

if __name__ == "__main__":
    download_kaggle_dataset()
