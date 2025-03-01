#!/usr/bin/env python3
"""
MQTT Client Module for Doorbell Detection System
This module handles MQTT communication for the doorbell detection system.
It provides a clean interface to connect, publish and subscribe to MQTT topics.
"""

import os
import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mqtt_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MQTTClient")

# Load environment variables
load_dotenv()

# MQTT Configuration from environment
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'user')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'pass')
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'home/doorbell/detect')
CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'doorbell_detector_client')

class MQTTClient:
    """MQTT client for doorbell detection system"""
    
    def __init__(self, client_id=CLIENT_ID, broker=MQTT_BROKER, port=MQTT_PORT,
                username=MQTT_USERNAME, password=MQTT_PASSWORD, topic=MQTT_TOPIC):
        """Initialize the MQTT client with the given parameters"""
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.connected = False
        
        logger.info(f"MQTT client initialized with broker: {self.broker}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to the broker"""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from the broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_publish(self, client, userdata, mid):
        """Callback for when a message is published"""
        logger.debug(f"Message {mid} published successfully")
    
    def connect(self):
        """Connect to the MQTT broker"""
        try:
            self.client = mqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            # Set username and password if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = time.time() + 5.0
            while not self.connected and time.time() < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                logger.error("Connection timeout")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MQTT broker"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def publish(self, message, topic=None, qos=1, retain=False):
        """
        Publish a message to the MQTT broker
        
        Args:
            message: The message to publish
            topic: Optional topic override, uses default if None
            qos: Quality of Service (0, 1, or 2)
            retain: Whether the message should be retained
            
        Returns:
            bool: True if successful, False otherwise
        """
        if topic is None:
            topic = self.topic
            
        try:
            # Try with connected client first
            if self.client and self.connected:
                self.client.publish(topic, message, qos=qos, retain=retain)
                logger.info(f"Published message to {topic}: {message}")
                return True
            
            # Fall back to using single publish if client is not connected
            publish.single(
                topic, 
                message, 
                hostname=self.broker, 
                port=self.port,
                client_id=self.client_id,
                auth={'username': self.username, 'password': self.password} if self.username else None,
                qos=qos,
                retain=retain
            )
            logger.info(f"Published message to {topic} using single publish: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False


# Simple interface for direct use
def send_notification(message=None, topic=None):
    """
    Simplified interface to send a notification via MQTT
    
    Args:
        message: Message to send (default: "Doorbell detected!")
        topic: Topic to publish to (default: from env or 'alarma/detector')
    
    Returns:
        bool: True if successful, False otherwise
    """
    if message is None:
        message = "Doorbell detected!"
        
    try:
        client = MQTTClient()
        return client.publish(message, topic)
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

# Example usage if run directly
if __name__ == "__main__":
    # Create and connect client
    client = MQTTClient()
    if client.connect():
        # Publish a test message
        client.publish("Test message from MQTT client")
        time.sleep(1)  # Wait for message to be sent
        client.disconnect()
    else:
        print("Failed to connect to MQTT broker") 