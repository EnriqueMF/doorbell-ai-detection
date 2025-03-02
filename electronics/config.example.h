/*
 * ESP8266 Configuration Example
 * 
 * This is an example configuration file for the ESP8266 component of the Doorbell Detection System.
 * Copy this file to config.h and fill in your values.
 * 
 * WARNING: Never commit your actual config.h file with real credentials to version control!
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
// -----------------
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// MQTT Configuration
// -----------------
// The MQTT broker is the server that handles message routing between components
#define MQTT_BROKER "mqtt.example.com"
// Standard MQTT port is 1883 (unencrypted) or 8883 (encrypted)
#define MQTT_PORT 1883
// Authentication credentials for the MQTT broker
#define MQTT_USERNAME "your_username"
#define MQTT_PASSWORD "your_password"
// Topic where doorbell detection events will be published
#define MQTT_TOPIC "alarma/detector"
// Unique client ID for this ESP8266 instance
#define MQTT_CLIENT_ID "esp8266_doorbell_alert"

// Telegram Configuration
// ---------------------
// Your Telegram Bot Token (get from BotFather)
#define BOT_TOKEN "your_bot_token"
// Chat ID where notifications will be sent
#define CHAT_ID "your_chat_id"

// DFPlayer Mini Configuration
// --------------------------
// RX and TX pins for DFPlayer Mini
#define DFPLAYER_RX 5  // D1 on NodeMCU
#define DFPLAYER_TX 4  // D2 on NodeMCU
// Volume level (0-30)
#define DFPLAYER_VOLUME 25

// Debug Configuration
// ------------------
// Set to true to enable debug output to Serial
#define DEBUG true

#endif // CONFIG_H 