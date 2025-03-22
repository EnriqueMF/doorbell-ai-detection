#include <Arduino.h>
#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>
#include <ESP8266WiFi.h>
#include "CTBot.h"
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <Pinger.h>
#include "config.h"

// IMPORTANT: ArduinoJson v6.19.4 required (compatibility issues with v6.20.0+)

#define LED_PIN 1

CTBot miBot;
SoftwareSerial timbreSoftwareSerial(D1, D2); // RX, TX
DFRobotDFPlayerMini timbreDFPlayer;
Pinger pinger;
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsgTime = 0;
const unsigned long twoHours = 7200000; // 2 hours in milliseconds

// Test MQTT broker connectivity using Pinger
bool pingBroker() {
  IPAddress brokerIP;
  if(!brokerIP.fromString(mqtt_server)) {
    Serial.println("Error: Invalid broker IP");
    return false;
  }
  return pinger.Ping(brokerIP);
}

// MQTT reconnection and status publishing
void reconnect() {
  while (!client.connected()) {
    if (client.connect(mqtt_client_id, mqtt_user, mqtt_password)) {
      client.subscribe(mqtt_topic);
      client.publish(mqtt_status_topic, "ESP connected successfully");
    } else {
      delay(5000);
    }
  }
}

// MQTT message callback
void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (String(topic) == mqtt_topic && message == "Alarma activada") {
    timbreDFPlayer.play(1);
    miBot.sendMessage(CHAT_ID, "Doorbell ringing...");
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  timbreSoftwareSerial.begin(9600);

  if (connectWiFi()) {
    // Visual feedback for WiFi connection
    for(int i=0; i<2; i++) {
      digitalWrite(LED_BUILTIN, LOW);
      delay(500);
      digitalWrite(LED_BUILTIN, HIGH);
      delay(500);
    }

    if (!testTCPConnection() || !pingBroker()) {
      while(true) { delay(1000); }
    }
    
    setupMQTT();
    initializeDFPlayer();
    setupTelegramBot();
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Send status message every 2 hours
  unsigned long currentTime = millis();
  if (currentTime - lastMsgTime > twoHours) {
    miBot.sendMessage(CHAT_ID, "System status: OK");
    lastMsgTime = currentTime;
  }

  // Handle Telegram commands
  TBMessage msg;
  if (CTBotMessageText == miBot.getNewMessage(msg)) {
    String compareMsg(msg.text);
    compareMsg.toLowerCase();
   
    char char_array[compareMsg.length() + 1];
    strcpy(char_array, compareMsg.c_str());
   
    if (StrContains("+", char_array)) {
      miBot.sendMessage(msg.sender.id, "Increasing volume");
      timbreDFPlayer.volumeUp();
      delay(500);
      timbreDFPlayer.volumeUp();
    }
    if (StrContains("-", char_array)) {
      miBot.sendMessage(msg.sender.id, "Decreasing volume");
      timbreDFPlayer.volumeDown();
      delay(500);
      timbreDFPlayer.volumeDown();
    }
    if (StrContains("timbre", char_array)) {
      timbreDFPlayer.play(1);
      miBot.sendMessage(msg.sender.id, "Playing doorbell sound...");
    }
    if (StrContains("ip", char_array)) {
      miBot.sendMessage(msg.sender.id, "IP: " + WiFi.localIP().toString());
    }
  }
  delay(25000);
}

// WiFi connection with timeout
bool connectWiFi() {
  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    delay(500);
  }
  return WiFi.status() == WL_CONNECTED;
}

// Test TCP connection to MQTT broker
bool testTCPConnection() {
  WiFiClient testClient;
  if (testClient.connect(mqtt_server, mqtt_port)) {
    testClient.stop();
    return true;
  }
  return false;
}

// Initialize DFPlayer with retry mechanism
void initializeDFPlayer() {
  int attempts = 0;
  bool initialized = false;
  while (attempts < 10 && !initialized) {
    digitalWrite(LED_BUILTIN, LOW);
    delay(5000);
    digitalWrite(LED_BUILTIN, HIGH);
    if (timbreDFPlayer.begin(timbreSoftwareSerial)) {
      // Set initial volume
      for(int i=0; i<4; i++) {
        timbreDFPlayer.volumeDown();
        delay(500);
      }
      timbreDFPlayer.play(1);
      initialized = true;
    } else {
      attempts++;
      delay(3000);
    }
  }
}

// Setup Telegram bot with retry mechanism
void setupTelegramBot() {
  miBot.setTelegramToken(token);
  bool connected = false;
  int attempts = 0;
  while (!connected && attempts < 10) {
    if (miBot.testConnection()) {
      connected = true;
    } else {
      attempts++;
      delay(3000);
    }
  }
}

// Setup MQTT client
void setupMQTT() {
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setKeepAlive(3600);
  reconnect();
}

// String search utility
bool StrContains(const char *str, const char *sfind) {
  char found = 0;
  char index = 0;
  char len = strlen(str);
  
  if (strlen(sfind) > len) return false;
  
  while (index < len) {
    if (str[index] == sfind[found]) {
      found++;
      if (strlen(sfind) == found) return true;
    } else {
      found = 0;
    }
    index++;
  }
  return false;
} 