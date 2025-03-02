#!/bin/bash
#
# Setup script for Doorbell Detection System on Orange Pi Zero3
# This script installs all required dependencies and sets up the system
#
# IMPORTANT: Configure the variables before running the script
#

# TODO(#1): Implement loading of environment variables from .env file

set -e  # Exit on error

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[*] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# CONFIGURATION - Modify these variables before running the script
# ----------------------------------------------------------------------
# MQTT Configuration
mqtt_broker=
mqtt_port=1883
mqtt_username=
mqtt_password=
mqtt_topic="home/doorbell/detect"

# Audio Configuration
audio_device_index=2
sample_rate=44100
detection_threshold=0.5
# ----------------------------------------------------------------------

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Verify configuration variables
if [ -z "$mqtt_broker" ] || [ -z "$mqtt_username" ] || [ -z "$mqtt_password" ]; then
    print_warning "MQTT variables not configured!"
    print_warning "Please edit this script and set the variables at the top before running."
    print_warning "You can copy them from your .env file if you have one."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

print_message "Setting up Doorbell Detection System on Orange Pi Zero3"
print_message "Current directory: $SCRIPT_DIR"

# Update system packages
print_message "Updating system packages..."
apt update
apt upgrade -y

# Install system dependencies
print_message "Installing system dependencies..."
apt install -y python3 python3-pip python3-dev portaudio19-dev libsndfile1 \
    libasound-dev python3-numpy libatlas-base-dev git

# Check audio devices
print_message "Checking audio devices..."
echo "Available audio devices:"
arecord -l
echo ""
print_warning "If no capture devices are shown above, make sure your microphone is properly connected"

# Install Python dependencies
print_message "Installing Python dependencies (this may take some time)..."
pip3 install --upgrade pip
pip3 install numpy scipy matplotlib paho-mqtt sounddevice librosa tensorflow python-dotenv

# Create service directory and configuration
print_message "Setting up application directory..."
APP_DIR="/opt/doorbell_detector"
mkdir -p $APP_DIR
mkdir -p $APP_DIR/models
mkdir -p $APP_DIR/logs

# Copy files to the application directory
print_message "Copying application files..."
cp "$SCRIPT_DIR/doorbell_detector.py" "$APP_DIR/"
cp "$SCRIPT_DIR/mqtt_client.py" "$APP_DIR/"
cp "$SCRIPT_DIR/config.json" "$APP_DIR/"
chmod +x "$APP_DIR/doorbell_detector.py"

# Create .env file
print_message "Creating .env configuration file in $APP_DIR..."
cat > "$APP_DIR/.env" << EOL
# Doorbell Detection Project Environment Variables
# WARNING: This file contains sensitive information and should not be committed to version control

# MQTT Configuration
MQTT_BROKER=${mqtt_broker}
MQTT_PORT=${mqtt_port}
MQTT_USERNAME=${mqtt_username}
MQTT_PASSWORD=${mqtt_password}
MQTT_TOPIC=${mqtt_topic}

# Audio Configuration
AUDIO_DEVICE_INDEX=${audio_device_index}
SAMPLE_RATE=${sample_rate}
DETECTION_THRESHOLD=${detection_threshold}

# Model Path
MODEL_PATH=$APP_DIR/models/doorbell_model.h5
EOL

# Also save a copy of the .env file to the script directory for future reference
print_message "Saving a copy of .env to script directory for future reference..."
cp "$APP_DIR/.env" "$SCRIPT_DIR/.env"

# Set proper permissions
chmod 600 "$APP_DIR/.env"
chmod 600 "$SCRIPT_DIR/.env"

# Create the service file
print_message "Creating systemd service..."
cat > /etc/systemd/system/doorbell-detector.service << EOL
[Unit]
Description=Doorbell Sound Detection Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/doorbell_detector.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Enable the service
print_message "Enabling service to start on boot..."
systemctl daemon-reload
systemctl enable doorbell-detector.service

# Copy model if available
if [ -f "./doorbell_model.h5" ]; then
    print_message "Found model file, copying to application directory..."
    cp "./doorbell_model.h5" "$APP_DIR/models/"
else
    print_warning "No model file found. You need to copy your trained model to $APP_DIR/models/"
fi

print_message "Setup complete!"
print_message "To start the service now, run: sudo systemctl start doorbell-detector.service"
print_message "To check the service status, run: sudo systemctl status doorbell-detector.service"
print_message "Logs can be found at: $APP_DIR/logs/doorbell_detector.log"
print_message ""
print_message "Next steps:"
print_message "1. Edit the environment configuration at $APP_DIR/.env if needed"
print_message "2. Place your trained model at $APP_DIR/models/doorbell_model.h5"
print_message ""

read -p "Would you like to start the service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    print_message "Starting doorbell detector service..."
    systemctl start doorbell-detector.service
    systemctl status doorbell-detector.service
else
    print_message "Service not started. You can start it manually later."
fi

print_message "Thank you for installing the Doorbell Detection System!" 