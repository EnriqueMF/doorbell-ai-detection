# ESP8266 System Diagrams

This document contains diagrams illustrating how the ESP8266 component interacts with the rest of the doorbell detection system.

## System Diagram

```mermaid
graph TD
    subgraph "Doorbell Detection System"
        subgraph "Orange Pi Zero3"
            A[Microphone] -->|Captures Audio| B[doorbell_detector.py]
            B -->|Processes Audio| C[TensorFlow Model]
            C -->|Detects Doorbell| D[mqtt_client.py]
            D -->|Publishes Message| E[MQTT Broker]
        end
        
        subgraph "ESP8266"
            F[PubSubClient] -->|Subscribed to| E
            F -->|Receives Message| G[DFPlayer Mini]
            G -->|Plays Sound| H[Speaker]
            F -->|Notifies| I[Telegram Bot]
            I -->|Sends Message| J[Telegram User]
            J -->|Sends Commands| I
            I -->|Controls| G
        end
        
        E -->|"Message: Alarm activated"| F
    end
    
    style Orange Pi Zero3 fill:#E8E8E8,stroke:#000000,stroke-width:2px
    style ESP8266 fill:none,stroke:#000000,stroke-width:2px 
    style A fill:#000000,stroke:#000000,stroke-width:1px
    style B fill:#000000,stroke:#000000,stroke-width:1px
    style C fill:#000000,stroke:#000000,stroke-width:1px
    style D fill:#000000,stroke:#000000,stroke-width:1px
    style E fill:#000000,stroke:#000000,stroke-width:1px
    style F fill:#000000,stroke:#000000,stroke-width:1px
    style G fill:#000000,stroke:#000000,stroke-width:1px
    style H fill:#000000,stroke:#000000,stroke-width:1px
    style I fill:#000000,stroke:#000000,stroke-width:1px
    style J fill:#000000,stroke:#000000,stroke-width:1px
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant M as Microphone
    participant OP as Orange Pi (Detector)
    participant MQTT as MQTT Broker
    participant ESP as ESP8266
    participant DF as DFPlayer Mini
    participant T as Telegram
    participant U as User
    
    M->>OP: Captures sound
    OP->>OP: Processes audio with ML model
    OP->>OP: Detects doorbell
    OP->>MQTT: Publishes "Alarm activated"
    MQTT->>ESP: Sends message
    ESP->>DF: Activates audio playback
    ESP->>T: Sends notification
    T->>U: Notifies "Doorbell ringing..."
    U->>T: Sends command (e.g., "doorbell")
    T->>ESP: Transmits command
    ESP->>DF: Executes action (e.g., play sound)
```

## Data Flow Diagram

```mermaid
flowchart LR
    A[Orange Pi Zero3] -->|"MQTT: Alarm activated"| B[MQTT Broker]
    B -->|Message| C[ESP8266]
    C -->|Command| D[DFPlayer Mini]
    D -->|Audio| E[Speaker]
    C -->|Notification| F[Telegram API]
    F -->|Message| G[Telegram App]
    G -->|Command| F
    F -->|Command| C
    
    style A fill:#E8E8E8,stroke:#000000,stroke-width:1px
    style B fill:#F0F0F0,stroke:#000000,stroke-width:1px
    style C fill:#CCCCCC,stroke:#000000,stroke-width:1px
    style D fill:#FFFFFF,stroke:#000000,stroke-width:1px
    style E fill:#FFFFFF,stroke:#000000,stroke-width:1px
    style F fill:#F0F0F0,stroke:#000000,stroke-width:1px
    style G fill:#F0F0F0,stroke:#000000,stroke-width:1px
```

## ESP8266 State Diagram

```mermaid
stateDiagram-v2
    [*] --> Initialization
    Initialization --> Connecting_WiFi
    Connecting_WiFi --> WiFi_Error: Failure
    Connecting_WiFi --> Configuring_DFPlayer: Success
    WiFi_Error --> Retry
    Retry --> Connecting_WiFi
    
    Configuring_DFPlayer --> Connecting_MQTT: Success
    Configuring_DFPlayer --> DFPlayer_Error: Failure
    DFPlayer_Error --> Retry
    
    Connecting_MQTT --> Connecting_Telegram: Success
    Connecting_MQTT --> MQTT_Error: Failure
    MQTT_Error --> Retry
    
    Connecting_Telegram --> Waiting_For_Events: Success
    Connecting_Telegram --> Telegram_Error: Failure
    Telegram_Error --> Retry
    
    Waiting_For_Events --> Processing_MQTT: MQTT Message
    Waiting_For_Events --> Processing_Telegram: Telegram Message
    Waiting_For_Events --> Sending_Status: Timer
    
    Processing_MQTT --> Playing_Sound: "Alarm activated"
    Playing_Sound --> Sending_Notification
    Sending_Notification --> Waiting_For_Events
    
    Processing_Telegram --> Adjusting_Volume: "+" or "-" Command
    Processing_Telegram --> Playing_Sound: "doorbell" Command
    Processing_Telegram --> Sending_IP: "ip" Command
    
    Adjusting_Volume --> Waiting_For_Events
    Sending_IP --> Waiting_For_Events
    
    Sending_Status --> Waiting_For_Events
```

## ESP8266 Software Architecture

```mermaid
classDiagram
    class ESP8266_Doorbell {
        -WiFiClient espClient
        -PubSubClient mqttClient
        -CTBot telegramBot
        -SoftwareSerial dfPlayerSerial
        -DFRobotDFPlayerMini dfPlayer
        +setup()
        +loop()
        -connectWiFi()
        -initializeDFPlayer()
        -setupMQTT()
        -setupTelegramBot()
        -reconnectMQTT()
        -handleTelegramMessage()
        -handleMQTTMessage()
    }
    
    class MQTT_Handler {
        -PubSubClient client
        -String topic
        -String clientId
        +connect()
        +subscribe()
        +callback()
        +reconnect()
    }
    
    class Telegram_Handler {
        -CTBot bot
        -String token
        -String chatId
        +setup()
        +sendMessage()
        +processCommand()
    }
    
    class DFPlayer_Handler {
        -DFRobotDFPlayerMini player
        -SoftwareSerial serial
        +initialize()
        +play()
        +volumeUp()
        +volumeDown()
    }
    
    ESP8266_Doorbell --> MQTT_Handler
    ESP8266_Doorbell --> Telegram_Handler
    ESP8266_Doorbell --> DFPlayer_Handler
```