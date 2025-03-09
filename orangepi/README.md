# Orange Pi Zero3 Doorbell Detection System

## Overview

This directory contains the doorbell-ai components that run on the Orange Pi Zero3, which serves as the main audio processing and detection unit in the doorbell detection system. The Orange Pi captures audio in bucle from a connected microphone, processes it using a trained machine learning model, and sends notifications via MQTT when a doorbell sound is detected.

## Prerequisites

### Required MQTT Server Setup

**IMPORTANT**: A running MQTT broker is REQUIRED for this system to function. The MQTT broker acts as the central communication hub between the Orange Pi (detection unit) and the ESP8266 (notification unit). Without a properly configured MQTT server, the system will not work.

You have several options for setting up an MQTT broker:

1. **VPS Server** (Recommended):
   - Set up a VPS with your preferred provider (DigitalOcean, AWS, etc.)
   - Install and configure Mosquitto MQTT broker
   - Ensure the server is accessible from your network
   - Configure proper security (firewall rules, authentication)

2. **Local Server**:
   - Set up Mosquitto on a local machine (Raspberry Pi, desktop computer)
   - Must be always running and accessible on your network
   - Configure port forwarding if remote access is needed

3. **Public MQTT Broker** (Not recommended for production):
   - Only use for testing
   - No guaranteed uptime or security
   - Limited functionality

For detailed MQTT server setup instructions, refer to the [VPS MQTT Server Configuration Guide](../vps/README.md).

### Quick MQTT Server Test

Before proceeding with the installation, verify your MQTT broker is accessible:

```bash
# Install Mosquitto clients
sudo apt install mosquitto-clients

# Test subscribing to messages
mosquitto_sub -h [broker-address] -p 1883 -u [username] -P [password] -t "test/#" &

# Test publishing a message (in a new terminal)
mosquitto_pub -h [broker-address] -p 1883 -u [username] -P [password] -t "test" -m "test message"
```

If both commands work and you see the test message, your MQTT broker is properly configured.

## Hardware Requirements

- Orange Pi Zero3 (recommended 2GB+ RAM model)
- USB microphone with good sensitivity
- Stable internet connection (wired or wireless)
- Power supply (5V/2A recommended)

## Installation

### Quick Setup

The system can be quickly set up using the provided `setup.sh` script:

```bash
# Clone the repository (if not already done)
git clone https://github.com/EnriqueMF/doorbell-ai-detection.git
cd doorbell-ai

# Copy your trained model to the project directory
cp model_generated_with_model_training_component.h5 ./src/orangepi/

# Make the script executable
chmod +x src/orangepi/setup.sh

# Run the setup script with sudo permissions
sudo src/orangepi/setup.sh
```

### What the Setup Script Does

The `setup.sh` script automates the following tasks:

1. Updates the system packages
2. Installs required system dependencies (Python, PortAudio, etc.)
3. Installs Python libraries (TensorFlow, librosa, paho-mqtt, etc.)
4. Creates the application directory at `/opt/doorbell_detector/`
5. Creates a `.env` file based on the variables defined at the top of the script
6. Creates and enables a systemd service for auto-start on boot
7. Copies the trained model to the appropriate location

### Before Running Setup

**Important:** Before running the setup script, you need to edit it to set your MQTT credentials and other configuration variables:

1. Open the script in an editor:
   ```bash
   nano src/orangepi/setup.sh
   ```

2. Find the configuration section at the top of the file and update these variables:
   ```bash
   # CONFIGURACIÓN - Modifica estas variables antes de ejecutar el script
   # ----------------------------------------------------------------------
   # MQTT Configuration
   mqtt_broker=          # <- Set your MQTT broker address here
   mqtt_port=1883
   mqtt_username=        # <- Set your MQTT username here
   mqtt_password=        # <- Set your MQTT password here
   mqtt_topic="home/doorbell/detect"
   
   # Audio Configuration
   audio_device_index=2
   sample_rate=44100
   detection_threshold=0.5
   ```

3. Save the file and run the setup script as described above

The script will create two copies of your configured `.env` file:
- One in the application directory (`/opt/doorbell_detector/.env`)
- Another in the script directory for future reference

### Manual Installation

If you prefer to install components manually, follow these steps:

1. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-dev portaudio19-dev \
       libsndfile1 libasound-dev python3-numpy libatlas-base-dev git
   ```

2. Install Python dependencies:
   ```bash
   pip3 install numpy scipy matplotlib paho-mqtt sounddevice librosa tensorflow python-dotenv
   ```

3. Create application directory:
   ```bash
   sudo mkdir -p /opt/doorbell_detector/models
   sudo mkdir -p /opt/doorbell_detector/logs
   ```

4. Copy the application files:
   ```bash
   sudo cp doorbell_detector.py mqtt_client.py config.json /opt/doorbell_detector/
   sudo cp model_generated_with_model_training_component.h5 /opt/doorbell_detector/models/doorbell_model.h5
   ```

5. Set up your environment configuration (see Configuration section below)

6. Set up the systemd service manually

## Configuration

### Environment Variables (.env)

The system uses a `.env` file to store configuration values. These values are initially set in the `setup.sh` script and then saved to `/opt/doorbell_detector/.env`. Here's an explanation of the main configuration parameters:

```
# MQTT Configuration (REQUIRED)
MQTT_BROKER=mqtt.example.com    # IP address/hostname of your MQTT broker
MQTT_PORT=1883                  # Port of your MQTT broker (default: 1883)
MQTT_USERNAME=username          # Your MQTT authentication username
MQTT_PASSWORD=password          # Your MQTT authentication password
MQTT_TOPIC=home/doorbell/detect # Topic for publishing detection events

# Audio Configuration
AUDIO_DEVICE_INDEX=2            # Index of the audio input device
SAMPLE_RATE=44100               # Sampling rate for audio capture
DETECTION_THRESHOLD=0.5         # Probability threshold for positive detection

# Model Path
MODEL_PATH=/opt/doorbell_detector/models/doorbell_model.h5
```

**Important Notes:** 
1. For security reasons, always ensure that `.env` files are not committed to your repository.
2. The MQTT configuration is REQUIRED for the system to function. Make sure you have a running MQTT broker before proceeding with the installation.
3. The project includes a `.env.example` file that can be used as a template, but you should configure the actual variables in the `setup.sh` script before running it.

To find the correct audio device index, you can run:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

### Configuration Reference (config.json)

The `config.json` file serves as a reference configuration. Actual values are loaded from the `.env` file. The config file provides a more structured overview of all available configuration options and their default values.

## Components in Detail

### Doorbell Detector (`doorbell_detector.py`)

The doorbell detector is the core component responsible for:

1. **Audio Capture:** Continuously captures audio using PyAudio from the configured input device.

2. **Audio Processing:** 
   - Buffers audio data for analysis
   - Applies amplitude thresholding to filter out silence
   - Extracts audio features using librosa (spectral contrast, MFCCs, chroma)

3. **Sound Detection:**
   - Uses the pre-trained TensorFlow model to classify audio fragments
   - Implements cooldown periods to prevent rapid consecutive triggers
   - Applies a detection threshold to filter out uncertain predictions

4. **Notification:** Sends detection events to the MQTT broker

#### Technical Details

The detector uses a sliding window approach to analyze audio in real-time. When the amplitude exceeds a threshold, an audio fragment is processed through these steps:

1. **Preprocessing:** Normalizing the audio signal
2. **Feature Extraction:** 
   - Spectral contrast (energy concentration across frequency bands)
   - MFCCs (Mel-frequency cepstral coefficients)
   - Chroma features (12 semitone pitch classes)
3. **Model Inference:** The extracted features are fed into a TensorFlow model
4. **Post-processing:** Applying threshold and cooldown logic

### MQTT Client (`mqtt_client.py`)

The MQTT client module handles all communication with the MQTT broker:

1. **Connection Management:** Establishes and maintains a connection to the broker
2. **Message Publishing:** Sends doorbell detection events to the configured topic
3. **Reconnection Logic:** Automatically reconnects if the connection is lost
4. **Authentication:** Securely connects using username/password authentication

The module provides both a class-based interface (`MQTTClient`) for advanced usage and a simplified function interface (`send_notification`) for basic publishing.

## Troubleshooting

### Common Issues

#### No Audio Detection

1. Check if the USB microphone is correctly connected
2. Verify the audio device index in `.env` is correct
3. Test the microphone using:
   ```bash
   arecord -d 5 -f cd test.wav  # Records 5 seconds of audio
   aplay test.wav               # Plays back the recording
   ```

#### MQTT Connection Problems

1. Verify the MQTT broker address and port are correct
2. Check if the credentials in `.env` are valid
3. Test the MQTT connection using:
   ```bash
   mosquitto_pub -h [broker] -p [port] -u [username] -P [password] -t [topic] -m "test"
   ```

#### Service Not Starting

1. Check the service status:
   ```bash
   sudo systemctl status doorbell-detector.service
   ```
2. View the logs:
   ```bash
   sudo journalctl -u doorbell-detector.service
   ```
   or
   ```bash
   cat /opt/doorbell_detector/logs/doorbell_detector.log
   ```

### Logs

The application logs are stored in:
- `/opt/doorbell_detector/logs/doorbell_detector.log` - Main application log
- `/opt/doorbell_detector/logs/mqtt_client.log` - MQTT client log

## Service Management

### Basic Service Commands

```bash
# Start the service
sudo systemctl start doorbell-detector.service

# Stop the service
sudo systemctl stop doorbell-detector.service

# Restart the service
sudo systemctl restart doorbell-detector.service

# Check service status
sudo systemctl status doorbell-detector.service

# Enable service to start at boot
sudo systemctl enable doorbell-detector.service

# Disable service from starting at boot
sudo systemctl disable doorbell-detector.service
```

### View Real-time Logs

```bash
sudo journalctl -u doorbell-detector.service -f
```

## Advanced Customization

### Modifying Detection Parameters

To adjust the detection sensitivity:

1. Edit the `.env` file:
   ```bash
   sudo nano /opt/doorbell_detector/logs/.env
   ```
2. Change the `DETECTION_THRESHOLD` value (lower for more sensitivity)
3. Restart the service:
   ```bash
   sudo systemctl restart doorbell-detector.service
   ```

### Using a Different Model

1. Place your new model in the models directory:
   ```bash
   sudo cp model_generated_with_model_training_component.h5 /opt/doorbell_detector/models/
   ```
2. Update the `.env` file to point to the new model
3. Restart the service

## License

This component is released under the MIT License. See the LICENSE file in the main project directory for more information.

### MQTT Connection Issues (Critical)

If you're experiencing MQTT connection problems:

1. **Verify MQTT Broker Status**:
   ```bash
   # For local broker:
   sudo systemctl status mosquitto
   
   # Check broker logs:
   sudo tail -f /var/log/mosquitto/mosquitto.log
   ```

2. **Test MQTT Connectivity**:
   ```bash
   # Test connection
   mosquitto_sub -h [broker] -p 1883 -u [username] -P [password] -t "test/#"
   
   # In another terminal:
   mosquitto_pub -h [broker] -p 1883 -u [username] -P [password] -t "test" -m "test"
   ```

3. **Network Connectivity**:
   - Check if the broker is accessible from your network:
     ```bash
     ping [broker-address]
     telnet [broker-address] 1883
     ```
   - Verify firewall rules allow MQTT traffic (port 1883 by default)
   - Check if DNS resolution works (if using hostname)

4. **Authentication Issues**:
   - Verify credentials in `.env` match those configured in the broker
   - Check broker's ACL (Access Control List) configuration
   - Try connecting with different credentials to isolate the issue

5. **Monitor MQTT Traffic**:
   ```bash
   # Subscribe to all topics (useful for debugging)
   mosquitto_sub -h [broker] -p 1883 -u [username] -P [password] -t "#" -v
   ``` 