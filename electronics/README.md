# ESP8266 Telegram Doorbell System

This project implements a smart doorbell system using an ESP8266 microcontroller with Telegram notifications and MQTT integration. It uses a DFPlayer Mini for audio playback when triggered.

## Features

- **Doorbell Functionality**: Plays audio files when triggered
- **Telegram Integration**: Receive notifications and control the doorbell remotely
- **MQTT Integration**: Core communication system for doorbell detection events
- **Remote Control**: Adjust volume and trigger the doorbell via Telegram commands
- **Status Updates**: Sends periodic status updates to ensure system is operational

## Hardware Requirements

- ESP8266 (NodeMCU or similar)
- DFPlayer Mini MP3 module
- Micro SD card with audio files
- Speaker (8Ω recommended)
- Power supply
- Optional: Doorbell button

## Prerequisites

### Required MQTT Server Setup

**IMPORTANT**: This system REQUIRES a running MQTT broker to function. The MQTT broker is the central communication hub that enables the doorbell detection system to work. You have several options:

1. **VPS Server**:
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

## Wiring

- **DFPlayer Mini**:
  - VCC → 5V
  - GND → GND
  - RX → D2 (ESP8266 TX)
  - TX → D1 (ESP8266 RX)
  - SPK_1/SPK_2 → Speaker

- **LED Indicator** (optional):
  - Anode → GPIO1 through a resistor
  - Cathode → GND

## Software Dependencies

- Arduino IDE
- Libraries:
  - ESP8266WiFi
  - SoftwareSerial
  - DFRobotDFPlayerMini
  - CTBot (for Telegram)
  - ArduinoJson (version 6.19.4 or earlier)
  - PubSubClient (for MQTT)

## Setup Instructions

1. **MQTT Server Setup** (REQUIRED):
   - Ensure your MQTT broker is running and accessible
   - Note down the broker's IP address/hostname
   - Create credentials for the doorbell system
   - Test the broker connection:
     ```bash
     # Install mosquitto clients
     sudo apt install mosquitto-clients
     
     # Test connection
     mosquitto_sub -h [broker-address] -p 1883 -u [username] -P [password] -t "test/#"
     ```

2. **Prepare the SD Card**:
   - Format the SD card as FAT32
   - Create a folder named "mp3" in the root directory
   - Add the bell audio file as 0001.mp3

3. **Configuration**:
   - Copy `config.h.example` to `config.h`
   - Edit `config.h` with your:
     - WiFi credentials
     - MQTT broker details (REQUIRED)
     - Telegram bot token

4. **Telegram Bot Setup**:
   - Create a new bot using BotFather on Telegram
   - Get your bot token and add it to the configuration
   - Start a conversation with your bot
   - Get your chat ID (you can use tools like @userinfobot)

5. **Upload the Code**:
   - Open the project in Arduino IDE
   - Select the correct board and port
   - Upload the code to your ESP8266

## Usage

### MQTT Integration (Core Functionality)

The MQTT integration is the core communication system:
- System subscribes to topic defined in `MQTT_TOPIC`
- Receives doorbell detection events from the Orange Pi
- Triggers the doorbell sound when "Alarma activada" message is received
- Sends status updates back to the broker

### Telegram Commands

- `+` - Increase volume
- `-` - Decrease volume
- `timbre` - Trigger the doorbell sound
- `ip` - Get the current IP address of the device

## Troubleshooting

### MQTT Connection Issues (Critical)
1. Verify MQTT broker is running:
   ```bash
   systemctl status mosquitto
   ```
2. Check broker connectivity:
   ```bash
   mosquitto_pub -h [broker] -p 1883 -u [username] -P [password] -t test -m "test"
   ```
3. Verify credentials in `config.h`
4. Check network connectivity and firewall rules
5. Monitor MQTT logs:
   ```bash
   tail -f /var/log/mosquitto/mosquitto.log
   ```

### Other Issues
- **DFPlayer Not Initializing**: Check wiring and SD card format
- **WiFi Connection Issues**: Verify credentials and signal strength
- **Telegram Not Responding**: Check token and internet connectivity

## Notes

- The system sends a status message every 2 hours to confirm it's operational
- ArduinoJson version 6.20.0 has compatibility issues; use version 6.19.4 or earlier
- The default volume is set to a moderate level; adjust as needed using Telegram commands

## License

This project is released under the MIT License. 