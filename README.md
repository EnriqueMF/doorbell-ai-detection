# AI-Powered Doorbell Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

This project develops an AI-powered system that captures and analyzes audio to detect a specific doorbell sound. Using FFT (Fast Fourier Transform) and machine learning techniques, the system can discriminate the target doorbell from ambient noise, even in noisy environments.

When the doorbell is detected, the system sends an alert through an MQTT broker to connected devices, allowing for flexible notification options.

## 🏗️ System Architecture

![System Architecture](docs/images/architecture_diagram.png)

The system consists of several key components:

1. **Audio Capture & Processing (Orange Pi Zero3)**
   - Captures real-time audio via connected microphone
   - Runs the trained ML model for doorbell detection
   - Publishes detection events to MQTT broker

2. **MQTT Message Broker (VPS Server)**
   - Handles message routing between components
   - Maintains connection state and message delivery
   - Provides secure communication channel

3. **Alert System (ESP32)**
   - Subscribes to doorbell detection events
   - Triggers MP3 playback through connected speaker
   - Optionally activates other connected devices/alerts

## 🚀 Getting Started

### Prerequisites

- Orange Pi Zero3 with Ubuntu installed
- ESP32 development board
- VPS server (for MQTT broker)
- USB microphone
- Speaker and necessary components for MP3 playback
- Python 3.8+

### Installation

Detailed installation instructions are available for each component:

- [Orange Pi Zero3 Setup](docs/installation/orangepi_setup.md)
- [VPS MQTT Server Configuration](docs/installation/vps_mqtt_setup.md)
- [ESP32 Alert System Setup](docs/installation/esp32_setup.md)

### Security and Environment Variables

This project uses environment variables for sensitive configuration (MQTT credentials, server addresses, etc.) following security best practices:

- All sensitive information is stored in `.env` files which are not committed to the repository
- Example configuration templates are provided as `.env.example` files
- The setup scripts check for existing configuration files before prompting for new values
- Permissions on credential files are automatically set to be readable only by the owner

When deploying this system, make sure to:
1. Never commit `.env` files with real credentials to version control
2. Keep backups of your configuration in a secure location
3. Use strong, unique passwords for all services

## 📊 Model Training

The audio detection model is trained using various samples of the target doorbell sound recorded under different conditions:
- Different distances from the doorbell
- Various background noise levels
- Different times of day/environmental conditions

The training process is documented in Jupyter notebooks in the `notebooks/` directory.

## 🔧 Hardware Requirements

### Orange Pi Zero3
- Recommended: Orange Pi Zero3 with 1GB+ RAM
- Ubuntu 22.04 LTS or compatible Linux distribution
- USB microphone with good sensitivity

### ESP32
- ESP32 development board (ESP32-WROOM recommended)
- External speaker (8ohm, 0.5W minimum)
- MP3 player module (optional, can use built-in DAC)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

Project Link: [https://github.com/EnriqueMF/ai-doorbell-detection](https://github.com/EnriqueMF/ai-doorbell-detection)