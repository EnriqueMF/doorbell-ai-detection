#include <Arduino.h>
#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>
#include <ESP8266WiFi.h>
#include "CTBot.h"
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include "config.h"  // Include configuration file sited in same directory

// Pin definitions
#define LED_PIN 1
#define RX_PIN D1
#define TX_PIN D2

// Global objects
CTBot miBot;
SoftwareSerial timbreSoftwareSerial(RX_PIN, TX_PIN); // ESP8266 RX, TX
DFRobotDFPlayerMini timbreDFPlayer;
WiFiClient espClient;
PubSubClient client(espClient);

// Time variables
unsigned long lastMsgTime = 0;
const unsigned long STATUS_INTERVAL = 7200000; // 2 hours in milliseconds

// Function declarations
bool connectWiFi();
bool initializeDFPlayer();
void setupMQTT();
bool setupTelegramBot();
void reconnectMQTT();
void printDFPlayerDetail(uint8_t type, int value);
bool StrContains(const char* str1, char* str2);

// MQTT message callback
void callback(char* topic, byte* payload, unsigned int length) {
  // Convert payload to string
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Message received on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  Serial.println(message);

  if (String(topic) == MQTT_TOPIC && message == "Alarma activada") {
    timbreDFPlayer.play(1);
    miBot.sendMessage(TELEGRAM_CHAT_ID, "Timbre sonant...");
    Serial.println("Alarm activated");
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  timbreSoftwareSerial.begin(9600);

  if (connectWiFi()) {
    Serial.println("Connected to WiFi");
    
    if (initializeDFPlayer()) {
      Serial.println("DFPlayer initialized successfully");
    } else {
      Serial.println("Failed to initialize DFPlayer");
    }
    
    setupMQTT();
    
    if (setupTelegramBot()) {
      Serial.println("Telegram bot configured successfully");
    } else {
      Serial.println("Failed to configure Telegram bot");
    }
  } else {
    Serial.println("Failed to connect to WiFi");
    // Handle connectivity failure case
  }
}

void loop() {
  // MQTT connection management
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // Send status message every 2 hours
  unsigned long currentTime = millis();
  if (currentTime - lastMsgTime > STATUS_INTERVAL) {
    miBot.sendMessage(TELEGRAM_CHAT_ID, "System running correctly...");
    lastMsgTime = currentTime;
  }

  // Telegram message handling
  TBMessage msg;
  if (CTBotMessageText == miBot.getNewMessage(msg)) {
    Serial.println(msg.text);
    String compareMsg = msg.text;
    compareMsg.toLowerCase();
    
    int n = compareMsg.length();
    char char_array[n + 1];
    strcpy(char_array, compareMsg.c_str());
    
    if (StrContains("+", char_array)) {
      Serial.println("INCREASING VOLUME");
      miBot.sendMessage(msg.sender.id, "INCREASING VOLUME");
      timbreDFPlayer.volumeUp();
      delay(500);
      timbreDFPlayer.volumeUp();
    }

    if (StrContains("-", char_array)) {
      Serial.println("DECREASING VOLUME");
      miBot.sendMessage(msg.sender.id, "DECREASING VOLUME");
      timbreDFPlayer.volumeDown();
      delay(500);
      timbreDFPlayer.volumeDown();
    }

    if (StrContains("timbre", char_array)) {
      timbreDFPlayer.play(1);
      miBot.sendMessage(msg.sender.id, "Doorbell ringing...");
    } 

    if (StrContains("ip", char_array)) {
      miBot.sendMessage(msg.sender.id, "IP: " + WiFi.localIP().toString());
    }
  }
  
  delay(500); // Better performance
}

bool connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long startAttemptTime = millis();
  const unsigned long timeout = 10000; // 10 seconds timeout

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < timeout) {
    Serial.print(".");
    delay(500);
  }
  
  Serial.println();
  return WiFi.status() == WL_CONNECTED;
}

bool initializeDFPlayer() {
  const int maxAttempts = 5;
  int attempts = 0;
  
  while (attempts < maxAttempts) { 
    if (timbreDFPlayer.begin(timbreSoftwareSerial)) {
      // Set initial volume
      for (int i = 0; i < 4; i++) {
        timbreDFPlayer.volumeDown();
        delay(200);
      }
      return true;
    } else {
      Serial.println("Error initializing DFPlayer. Retrying...");
      attempts++;
      delay(1000);
    }
  }
  return false;
}

bool setupTelegramBot() {
  miBot.setTelegramToken(TELEGRAM_TOKEN);
  const int maxAttempts = 3;
  int attempts = 0;

  while (attempts < maxAttempts) {
    if (miBot.testConnection()) {
      return true;
    } else {
      attempts++;
      Serial.println("Failed to connect to Telegram. Retrying...");
      delay(2000);
    }
  }
  return false;
}

void setupMQTT() {
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
  reconnectMQTT();
}

void reconnectMQTT() {
  const int maxAttempts = 3;
  int attempts = 0;
  
  while (!client.connected() && attempts < maxAttempts) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("Connected to MQTT");
      client.subscribe(MQTT_TOPIC);
      return;
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 3 seconds");
      attempts++;
      delay(3000);
    }
  }
  
  if (attempts >= maxAttempts) {
    Serial.println("Could not connect to MQTT after several attempts");
  }
}

// Function to print DFPlayer details
void printDFPlayerDetail(uint8_t type, int value) {
  switch (type) {
    case TimeOut:
      Serial.println(F("Time Out!"));
      break;
    case WrongStack:
      Serial.println(F("Stack Wrong!"));
      break;
    case DFPlayerCardInserted:
      Serial.println(F("Card Inserted!"));
      break;
    case DFPlayerCardRemoved:
      Serial.println(F("Card Removed!"));
      break;
    case DFPlayerCardOnline:
      Serial.println(F("Card Online!"));
      break;
    case DFPlayerUSBInserted:
      Serial.println("USB Inserted!");
      break;
    case DFPlayerUSBRemoved:
      Serial.println("USB Removed!");
      break;
    case DFPlayerPlayFinished:
      Serial.print(F("Number:"));
      Serial.print(value);
      Serial.println(F(" Play Finished!"));
      break;
    case DFPlayerError:
      Serial.print(F("DFPlayerError:"));
      switch (value) {
        case Busy:
          Serial.println(F("Card not found"));
          break;
        case Sleeping:
          Serial.println(F("Sleeping"));
          break;
        case SerialWrongStack:
          Serial.println(F("Get Wrong Stack"));
          break;
        case CheckSumNotMatch:
          Serial.println(F("Check Sum Not Match"));
          break;
        case FileIndexOut:
          Serial.println(F("File Index Out of Bound"));
          break;
        case FileMismatch:
          Serial.println(F("Cannot Find File"));
          break;
        case Advertise:
          Serial.println(F("In Advertise"));
          break;
        default:
          break;
      }
      break;
    default:
      break;
  }
}

// Helper function to search for substrings
bool StrContains(const char* str1, char* str2) {
  // Implementation of StrContains function
  if (strstr(str2, str1) != NULL) {
    return true;
  }
  return false;
} 