# Makefile for doorbell detection model training (Linux only)

# Unix commands
RM_CMD = rm -rf __pycache__
RM_IPYNB_CMD = rm -rf .ipynb_checkpoints
MKDIR_CMD = mkdir -p $(1)
PYTHON_CMD = python3
JUPYTER_CMD = jupyter

# Get Python version for venv package
PYTHON_VERSION := $(shell $(PYTHON_CMD) --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_VENV_PKG = python$(PYTHON_VERSION)-venv

# Unix venv commands
VENV_ACTIVATE = source venv/bin/activate
PIP_CMD = ./venv/bin/pip
VENV_JUPYTER = ./venv/bin/jupyter

# Targets
.PHONY: all setup install test clean venv run

# Default target
all: setup

# Setup
setup: system-deps venv
	$(PIP_CMD) install -r requirements.txt

# Install system dependencies
system-deps:
	sudo apt-get update
	sudo apt-get install -y python3-dev libasound2-dev libsndfile1-dev $(PYTHON_VENV_PKG)
	@echo "System dependencies installed successfully."

# Create virtual environment
venv: system-deps
	$(PYTHON_CMD) -m venv venv
	@echo "Virtual environment created. Activate with: $(VENV_ACTIVATE)"

# Install Python dependencies only
install:
	$(PIP_CMD) install -r requirements.txt

# Test the environment
test:
	$(PYTHON_CMD) -c "import librosa, tensorflow; print('Environment configured correctly')"

# Clean temporary files
clean:
	$(RM_CMD)
	$(RM_IPYNB_CMD)
	find . -type f -name "*.pyc" -delete

# Run the Jupyter notebook
run:
	$(VENV_JUPYTER) notebook doorbell_detection_training.ipynb