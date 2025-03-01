#!/usr/bin/env python3
"""
Doorbell Sound Detection for Orange Pi Zero 3
This script captures audio in real-time, processes it with a pre-trained model,
and sends MQTT notifications when a doorbell sound is detected.

"""

import os
import sys
import time
import signal
import json
import logging
import numpy as np
import pyaudio
import librosa
from scipy.fftpack import fft
import tensorflow as tf
from dotenv import load_dotenv
from mqtt_client import MQTTClient, send_notification

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("doorbell_detector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DoorbellDetector")

# Load environment variables
load_dotenv()

# Configuration from environment variables
DEVICE_INDEX = int(os.getenv('AUDIO_DEVICE_INDEX', 2))
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 44100))
DETECTION_THRESHOLD = float(os.getenv('DETECTION_THRESHOLD', 0.5))
MODEL_PATH = os.getenv('MODEL_PATH', '/opt/doorbell_detector/models/doorbell_model.h5')

# Audio capture parameters
CHUNK_SIZE = 512
CHANNELS = 1
FORMAT = pyaudio.paInt16
AMPLITUDE_THRESHOLD = 2300  # Minimum amplitude to trigger analysis
BUFFER_DURATION = 5  # Duration in seconds of audio buffer

class DoorbellDetector:
    """
    Real-time audio processing for doorbell detection.
    Captures audio, analyzes it, and sends notifications when doorbell is detected.
    """
    
    def __init__(self):
        self.model = None
        self.audio = None
        self.stream = None
        self.mqtt_client = None
        self.running = False
        self.audio_buffer = np.array([])
        self.last_notification_time = 0
        self.cooldown_period = 10  # Time between notifications in seconds
        self.last_detection_time = 0
        self.consecutive_detections = 0
        self.consecutive_required = 2
        
        logger.info("DoorbellDetector initialized")
        
    def load_model(self):
        """Load the pre-trained model"""
        try:
            logger.info(f"Loading model from {MODEL_PATH}")
            self.model = tf.keras.models.load_model(MODEL_PATH)
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
            
    def initialize_audio(self):
        """Initialize the audio capture"""
        try:
            logger.info("Initializing audio capture")
            self.audio = pyaudio.PyAudio()
            
            # List available audio devices
            logger.info("Available audio devices:")
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                logger.info(f"Device {i}: {device_info['name']}")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=DEVICE_INDEX,
                frames_per_buffer=CHUNK_SIZE
            )
            
            logger.info(f"Audio capture initialized with device index {DEVICE_INDEX}")
            return True
        except Exception as e:
            logger.error(f"Error initializing audio: {e}")
            return False
    
    def initialize_mqtt(self):
        """Initialize MQTT client"""
        try:
            logger.info("Initializing MQTT client")
            self.mqtt_client = MQTTClient()
            success = self.mqtt_client.connect()
            if success:
                logger.info("MQTT client connected successfully")
            else:
                logger.warning("MQTT client failed to connect")
            return success
        except Exception as e:
            logger.error(f"Error initializing MQTT: {e}")
            return False
    
    def extract_features(self, audio_data):
        """
        Extract audio features for the model
        
        Args:
            audio_data: Audio signal
            
        Returns:
            Feature vector or None if error
        """
        try:
            # Normalize audio
            audio_data = audio_data.astype(np.float32) / np.max(np.abs(audio_data))
            
            # Spectral contrast
            spec_contrast = librosa.feature.spectral_contrast(y=audio_data, sr=SAMPLE_RATE)
            spec_contrast_processed = np.mean(spec_contrast.T, axis=0)
            
            # MFCC
            mfcc = librosa.feature.mfcc(y=audio_data, sr=SAMPLE_RATE, n_mfcc=13)
            mfcc_processed = np.mean(mfcc.T, axis=0)
            
            # Chroma feature
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=SAMPLE_RATE)
            chroma_processed = np.mean(chroma.T, axis=0)
            
            # Concatenate all features
            features = np.concatenate([
                spec_contrast_processed,
                mfcc_processed,
                chroma_processed
            ])
            
            return features
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def analyze_audio(self, audio_fragment):
        """
        Analyze an audio fragment to detect doorbell
        
        Args:
            audio_fragment: Audio data to analyze
            
        Returns:
            tuple: (is_detected, probability)
        """
        try:
            features = self.extract_features(audio_fragment)
            if features is None:
                return False, 0.0
                
            # Add batch dimension and predict
            features_batch = np.expand_dims(features, axis=0)
            prediction = self.model.predict(features_batch)[0][0]
            
            is_detected = prediction > DETECTION_THRESHOLD
            
            if is_detected:
                logger.info(f"Doorbell detected with probability: {prediction:.4f}")
                current_time = time.time()
                
                # Track consecutive detections
                if current_time - self.last_detection_time < 2:  # Within 2 seconds
                    self.consecutive_detections += 1
                else:
                    self.consecutive_detections = 1
                
                self.last_detection_time = current_time
                
                # Only trigger notification if enough consecutive detections
                if self.consecutive_detections >= self.consecutive_required:
                    return True, prediction
            else:
                # Reset consecutive detections if below threshold
                self.consecutive_detections = 0
            
            return False, prediction
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            return False, 0.0
    
    def process_audio(self):
        """Process audio in real-time and detect doorbell"""
        if not self.stream:
            logger.error("Audio stream not initialized")
            return
            
        try:
            logger.info("Starting audio processing...")
            buffer_size = int(SAMPLE_RATE * BUFFER_DURATION)
            self.audio_buffer = np.zeros(buffer_size, dtype=np.int16)
            buffer_index = 0
            
            while self.running:
                # Read audio chunk
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Add to circular buffer
                end_index = min(buffer_index + len(audio_chunk), buffer_size)
                chunk_to_copy = audio_chunk[:end_index - buffer_index]
                self.audio_buffer[buffer_index:end_index] = chunk_to_copy
                
                # If buffer wraps around
                if end_index - buffer_index < len(audio_chunk):
                    remaining = len(audio_chunk) - (end_index - buffer_index)
                    self.audio_buffer[:remaining] = audio_chunk[-(remaining):]
                    buffer_index = remaining
                else:
                    buffer_index = end_index % buffer_size
                
                # Check amplitude to save processing
                max_amplitude = np.max(np.abs(audio_chunk))
                if max_amplitude > AMPLITUDE_THRESHOLD:
                    # Get the full buffer for analysis
                    analysis_buffer = np.concatenate([
                        self.audio_buffer[buffer_index:],
                        self.audio_buffer[:buffer_index]
                    ])
                    
                    # Analyze the audio
                    is_detected, probability = self.analyze_audio(analysis_buffer)
                    
                    # Handle detection
                    if is_detected:
                        self.send_notification(probability)
                
                # Small sleep to reduce CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("Audio processing stopped by user")
        except Exception as e:
            logger.error(f"Error in audio processing: {e}")
    
    def send_notification(self, probability):
        """Send MQTT notification when doorbell is detected"""
        current_time = time.time()
        if current_time - self.last_notification_time < self.cooldown_period:
            logger.info("Notification in cooldown period, skipping")
            return False
            
        try:
            self.last_notification_time = current_time
            message = json.dumps({
                "event": "doorbell_detected",
                "timestamp": time.time(),
                "probability": float(probability),
                "device": "orange_pi_zero3"
            })
            
            if self.mqtt_client and self.mqtt_client.connected:
                success = self.mqtt_client.publish(message)
            else:
                success = send_notification(message)
                
            if success:
                logger.info("Notification sent successfully")
            else:
                logger.warning("Failed to send notification")
                
            return success
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info("Termination signal received, stopping...")
        self.running = False
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        if self.audio:
            self.audio.terminate()
            
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            
        logger.info("Cleanup complete")
    
    def start(self):
        """Start the doorbell detection system"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Initialize components
        if not self.load_model():
            logger.error("Failed to load model, exiting")
            return False
            
        if not self.initialize_audio():
            logger.error("Failed to initialize audio, exiting")
            return False
            
        self.initialize_mqtt()  # Continue even if MQTT fails
        
        # Start processing
        self.running = True
        try:
            self.process_audio()
        finally:
            self.cleanup()
            
        return True


def main():
    """Main entry point"""
    logger.info("Starting doorbell detection system")
    processor = DoorbellDetector()
    success = processor.start()
    if success:
        logger.info("Doorbell detection completed successfully")
        return 0
    else:
        logger.error("Doorbell detection failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 