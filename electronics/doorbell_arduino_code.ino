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

bool is_subscribed = false;

// Test MQTT broker connectivity using Pinger
bool pingBroker() {
  IPAddress brokerIP;
  if(!brokerIP.fromString(mqtt_server)) {
    Serial.println("Error: IP del broker no válida");
    return false;
  }
  Serial.print("Haciendo ping al broker (");
  Serial.print(brokerIP);
  Serial.println(")...");
  if(pinger.Ping(brokerIP) == false) {
    Serial.println("Ping fallido.");
    return false;
  }
  Serial.println("Ping exitoso.");
  return true;
}

// MQTT reconnection and status publishing
void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");
    if (client.connect("timbre_tema_id", mqtt_user, mqtt_password)) {
      Serial.println("Conectado a MQTT");
      if (is_subscribed == false) {
        client.subscribe("alarma/detector");
        is_subscribed = true;
      }
      client.publish("esp/status", "ESP conectado correctamente");
    } else {
      Serial.print("Fallo en conexión MQTT. Estado=");
      Serial.print(client.state());
      Serial.println(" Intentando de nuevo en 5 segundos");
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
 
  Serial.print("Mensaje recibido bajo el tópico: ");
  Serial.print(topic);
  Serial.print(". Mensaje: ");
  Serial.println(message);

  if (String(topic) == "alarma/detector") {
    if (message == "Alarma activada") {
      timbreDFPlayer.play(1);
      miBot.sendMessage(-4116655447, "Timbre sonant...");
      Serial.println("Alarma activada");
    }
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
    miBot.sendMessage(-4116655447, "Estado correcto...");
    lastMsgTime = currentTime;
  }

  // Handle Telegram commands
  static unsigned long lastTelegramCheck = 0;
  if (currentTime - lastTelegramCheck >= 25000) {
    TBMessage msg;
    if (CTBotMessageText == miBot.getNewMessage(msg)) {
      Serial.println(msg.text);
      String compareMsg(msg.text);
      compareMsg.toLowerCase();
      int n = compareMsg.length();
      char char_array[n + 1];
      strcpy(char_array, compareMsg.c_str());
      
      if (StrContains("+", char_array)) {
        Serial.println("SUBIR VOLUMEN");
        miBot.sendMessage(msg.sender.id, "SUBIENDO VOLUMEN");
        timbreDFPlayer.volumeUp();
        delay(500);  // Para evitar múltiples incrementos en un solo comando
        timbreDFPlayer.volumeUp();
      }
      if (StrContains("-", char_array)) {
        Serial.println("BAJAR VOLUMEN");
        miBot.sendMessage(msg.sender.id, "BAJANDO VOLUMEN");
        timbreDFPlayer.volumeDown();
        delay(500);  // Del mismo modo, breve pausa
        timbreDFPlayer.volumeDown();
      }
      if (StrContains("timbre", char_array)) {
        timbreDFPlayer.play(1);
        miBot.sendMessage(msg.sender.id, "Timbre sonando...");
      }
      if (StrContains("ip", char_array)) {
        miBot.sendMessage(msg.sender.id, "IP: " + WiFi.localIP().toString(), "");
      }
    }
    lastTelegramCheck = currentTime;
  }
}

// WiFi connection with timeout
bool connectWiFi() {
  Serial.print("Conectando a WiFi...");
  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    Serial.print(".");
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
  int intentos = 0;
  bool inicializado = false;
  int max_intentos = 10;
  while (intentos < max_intentos && !inicializado) {
    client.publish("esp/status", "Intentando conexión DFPlayer...");
    digitalWrite(LED_BUILTIN, LOW);
    delay(5000);
    digitalWrite(LED_BUILTIN, HIGH);
    if (timbreDFPlayer.begin(timbreSoftwareSerial)) {
      Serial.println("DFPlayer inicializado correctamente");
      client.publish("esp/status", "DFPlayer conectado correctamente");
      delay(500);
      timbreDFPlayer.volumeDown();
      delay(500);
      timbreDFPlayer.volumeDown();
      delay(500);
      timbreDFPlayer.volumeDown();
      delay(500);
      timbreDFPlayer.volumeDown();
      delay(500);
      Serial.println("Reproduciendo el primer MP3...");
      client.publish("esp/status", "Reproduciendo el primer MP3..."); 
      timbreDFPlayer.play(1);
      inicializado = true;
    } else {
      Serial.println("Error en la inicialización del DFPlayer");
      Serial.println("Reintentando....");
      client.publish("esp/status", "Error al inicializar DFPlayer, reintentando...");
      intentos++;
      delay(3000);
    }
  }
  if (!inicializado) {
    Serial.println("No se pudo inicializar el DFPlayer después de varios intentos");
    client.publish("esp/status", "DFPlayer fallo al inicializarse");
  }
}

// Setup Telegram bot with retry mechanism
void setupTelegramBot() {
  miBot.setTelegramToken(token);
  bool conectado = false;
  int intentos = 0;
  const int maxIntentos = 10;
  while (!conectado && intentos < maxIntentos) {
    if (miBot.testConnection()) {
      Serial.println("\nConectado a Telegram");
      client.publish("esp/status", "Conectado a Telegram..."); 
      conectado = true;
    } else {
      intentos++;
      Serial.println("\nFallo al conectar con Telegram, reintentando...");
      delay(3000);
    }
  }
  if (!conectado) {
    Serial.println("\nNo se pudo conectar con Telegram después de varios intentos");
  }
}

// Setup MQTT client
void setupMQTT() {
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setKeepAlive(10);
  reconnect();
}

// String search utility
bool StrContains(const char *str, const char *sfind) {
  char found = 0;
  char index = 0;
  char len;
  len = strlen(str);
  if (strlen(sfind) > len) {
    return false;
  }
  while (index < len) {
    if (str[index] == sfind[found]) {
      found++;
      if (strlen(sfind) == found) {
        return true;
      }
    } else {
      found = 0;
    }
    index++;
  }
  return false;
} 