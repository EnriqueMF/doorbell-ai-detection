# Makefile for doorbell detection model training
# Uses conda for environment management

.PHONY: help setup-conda install-deps clean run-jupyter install-all-conda

# Variables
PYTHON_VERSION = 3.8
PIP_PACKAGES = jupyter notebook matplotlib gdown
CONDA_PACKAGES = numpy tensorflow scikit-learn librosa soundfile

help:
	@echo "Available commands:"
	@echo "  make help             - Show this help"
	@echo "  make setup-conda      - Set up conda environment"
	@echo "  make install-deps     - Install dependencies in active environment"
	@echo "  make install-all-conda  - Set up everything with conda (recommended)"
	@echo "  make clean            - Remove temporary files and caches"
	@echo "  make run-jupyter      - Start Jupyter notebook server"
	@echo "  make download-audio   - Download audio files from Google Drive"

# Setup with conda
setup-conda:
	@echo "Setting up conda environment..."
	conda create -y -n doorbell_detector python=$(PYTHON_VERSION)
	@echo "Activate the environment with: conda activate doorbell_detector"

# Install dependencies
install-deps:
	@echo "Installing dependencies..."
	pip install $(PIP_PACKAGES)
	conda install -y $(CONDA_PACKAGES)

# Complete installation with conda (recommended)
install-all-conda: setup-conda
	@echo "Installing all dependencies with conda..."
	conda install -y -n doorbell_detector -c conda-forge $(CONDA_PACKAGES)
	conda run -n doorbell_detector pip install $(PIP_PACKAGES)
	@echo "\nEnvironment successfully configured!"
	@echo "To activate the environment: conda activate doorbell_detector"
	@echo "To run Jupyter: make run-jupyter"

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	rm -rf __pycache__
	rm -rf .ipynb_checkpoints
	find . -name "*.pyc" -delete

# Run Jupyter
run-jupyter:
	@echo "Starting Jupyter Notebook..."
	jupyter notebook ../model_training/doorbell_detection_training.ipynb

# Instructions for downloading files
download-audio:
	@echo "Downloading audio files..."
	mkdir -p ../audio_samples
	python -c "import gdown; gdown.download_folder('https://drive.google.com/drive/folders/1U7N5TEEiXGxcgeGYuU2cLPp3nGQB0fGQ', output='../audio_samples', quiet=False, use_cookies=False)" 