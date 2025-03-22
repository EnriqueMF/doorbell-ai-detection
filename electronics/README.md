# ESP8266 Telegram Doorbell System

This project implements a smart doorbell system using an ESP8266 microcontroller with Telegram notifications and MQTT integration. It uses a DFPlayer Mini for audio playback when triggered.

## Features

- **Doorbell Functionality**: Plays audio files (e.g., "001.mp3") when triggered
- **Telegram Integration**: Receive notifications and control the doorbell remotely
- **MQTT Integration**: Core communication system for detection events and status updates
- **Remote Control**: Adjust volume and trigger the doorbell via Telegram commands
- **Status Updates**: Sends periodic status updates every 2 hours to confirm system operation
- **Connectivity Verification**: Tests MQTT broker connectivity using Pinger library before establishing connection
- **Extended Keepalive**: Configured with 60-second keepalive interval to minimize disconnections

## Hardware Requirements

- ESP8266 (NodeMCU or similar)
- DFPlayer Mini MP3 module
- Micro SD card with audio files
- Speaker (8Ω recommended)
- Power supply
- Optional: Doorbell button

## Software Dependencies

### Required Libraries

- **ESP8266WiFi**: Built-in library for WiFi connectivity
- **PubSubClient** (>=2.8.0): For MQTT communication
- **CTBot** (>=2.1.9): For Telegram bot functionality
- **ArduinoJson** (6.19.4): For JSON parsing (IMPORTANT: Use version 6.19.4, newer versions may have compatibility issues with CTBot)
- **DFRobotDFPlayerMini** (>=1.0.5): For MP3 player control
- **SoftwareSerial**: Built-in library for serial communication with DFPlayer
- **Pinger**: For MQTT broker connectivity verification

### Arduino IDE Setup

1. Add ESP8266 board support:
   - Open Arduino IDE → Preferences
   - Add URL to Additional Boards Manager URLs:
     ```
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Tools → Board → Boards Manager
   - Search for "esp8266" and install

2. Board Configuration:
   - Board: "NodeMCU 1.0 (ESP-12E Module)"
   - CPU Frequency: "80 MHz"
   - Flash Size: "4MB (FS:2MB OTA:~1019KB)"
   - Upload Speed: "115200"

## MQTT Server Setup (REQUIRED)

The MQTT broker is **ESSENTIAL** for the system to function. You have several options:

### 1. VPS Server (Recommended)
- Set up a VPS with your preferred provider
- Install Mosquitto MQTT broker:
  ```bash
  sudo apt update
  sudo apt install mosquitto mosquitto-clients
  sudo systemctl enable mosquitto
  ```
- Configure authentication:
  ```bash
  sudo mosquitto_passwd -c /etc/mosquitto/passwd your_username
  ```
- Edit `/etc/mosquitto/conf.d/default.conf`:
  ```
  listener 1883
  password_file /etc/mosquitto/passwd
  allow_anonymous false
  ```
- **Important**: Open port 1883 in VPS firewall (e.g., using UFW):
  ```bash
  sudo ufw allow 1883/tcp
  ```
- Restart Mosquitto:
  ```bash
  sudo systemctl restart mosquitto
  ```

### 2. Local Server
- Install Mosquitto on a local machine:
  ```bash
  sudo apt install mosquitto mosquitto-clients
  ```
- Follow same configuration steps as VPS
- Configure port forwarding if needed
- Ensure the server is always running

### 3. Public MQTT Broker (Testing Only)
- Only use for development/testing
- No guaranteed uptime or security
- Examples:
  - test.mosquitto.org
  - broker.hivemq.com
  - iot.eclipse.org

### Testing MQTT Connection

```bash
# Subscribe to test topic
mosquitto_sub -h [broker-address] -p 1883 -u [username] -P [password] -t "test/#"

# Publish test message
mosquitto_pub -h [broker-address] -p 1883 -u [username] -P [password] -t test -m "test"
```

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

## Setup Instructions

1. **MQTT Server Setup** (REQUIRED):
   - Ensure your MQTT broker is running and accessible
   - Open port 1883 in VPS firewall (if using VPS)
   - Create credentials for the doorbell system
   - Test the broker connection:
     ```bash
     # Install mosquitto clients
     sudo apt install mosquitto-clients
     
     # Test connection and verify status messages
     mosquitto_sub -h [broker-address] -t "esp/status" -u [username] -P [password]
     ```
   - You should see "ESP connected successfully" when the ESP8266 connects

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
- System subscribes to topic "alarma/detector"
- Receives doorbell detection events from the Orange Pi
- Triggers the doorbell sound when "Alarma activada" message is received
- Publishes status messages to "esp/status" topic
- Implements extended keepalive (60 seconds) for connection stability
- Verifies broker connectivity before establishing connection

### Telegram Commands

- `+` - Increase volume
- `-` - Decrease volume
- `timbre` - Trigger the doorbell sound
- `ip` - Get the current IP address of the device

## Troubleshooting

### MQTT Connection Issues (Critical)

1. **Verify MQTT Broker Status**:
   ```bash
   sudo systemctl status mosquitto
   ```

2. **Check Firewall Configuration**:
   ```bash
   sudo ufw status
   # If port 1883 is not open:
   sudo ufw allow 1883/tcp
   ```

3. **Test MQTT Connectivity**:
   ```bash
   # Subscribe to status messages
   mosquitto_sub -h [broker-address] -t "esp/status" -u [username] -P [password]
   ```

4. **Network Connectivity**:
   - Verify broker is reachable:
     ```bash
     ping [broker-address]
     telnet [broker-address] 1883
     ```
   - Check firewall rules allow MQTT traffic
   - Verify DNS resolution if using hostname

5. **Monitor MQTT Traffic**:
   ```bash
   # Subscribe to all topics (useful for debugging)
   mosquitto_sub -h [broker-address] -t "#" -v -u [username] -P [password]
   ```

### Other Issues
- **DFPlayer Not Initializing**: Check wiring and SD card format
- **WiFi Connection Issues**: Verify credentials and signal strength
- **Telegram Not Responding**: Check token and internet connectivity

## Notes

- The system sends a status message every 2 hours to confirm operation
- ArduinoJson version 6.19.4 is required (newer versions may have compatibility issues with CTBot)
- Extended keepalive interval (60 seconds) helps maintain stable MQTT connection
- Broker connectivity is verified using Pinger library before establishing connection
- Default volume is set to a moderate level; adjust using Telegram commands

## License

This project is released under the MIT License. 