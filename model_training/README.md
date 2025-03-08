# Doorbell Detection Model Training

This module trains a machine learning model to detect doorbell sounds from audio recordings.

## System Requirements

- Linux operating system (Ubuntu/Debian recommended)
- Python 3.8 or higher
- pip (Python package manager)

## Installation

This project is optimized for Linux systems.

### Installation with Makefile

The easiest way to set up everything is using the included Makefile. This will setup the complete environment (install system and Python dependencies):

```bash
make setup
```

This command:
1. Creates a Python virtual environment
2. Installs necessary system dependencies
3. Installs all required Python packages

### Manual Installation

If you prefer a manual installation:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev libasound2-dev libsndfile1-dev

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Verification

To verify that everything is installed and configured correctly:

```bash
make test
```

## Audio Data Preparation

### Recording Your Doorbell

To train an effective model, you need to record your specific doorbell sound:

1. **Record your doorbell**: Use any recording device.
2. **Name the file**: Save it as `doorbell.mp3` in the `../audio_samples/` directory.
3. **Add background audio**: Include various background noises in the same directory.

The system will automatically use `doorbell.mp3` as the positive sample and other audio files as background noise.


## Training the Model

Run the training notebook:

```bash
# Start the Jupyter notebook server
make run

# Or run it directly
jupyter notebook doorbell_detection_training.ipynb
```

## Output

After training, the model will be saved in two formats:

- TensorFlow model (`.h5`): For use with TensorFlow/Keras
- TensorFlow Lite model (`.tflite`): For deployment on embedded devices

Both models will be saved to the `../models/` directory.


## Additional Commands

Install only Python dependencies
```bash
make install
```

Clean temporary Python files
```bash
make clean
```