#!/usr/bin/env python3
"""
Sensor Agent - Part II.1
Publishes sensor readings at regular intervals on topic: /<zone>/<type>/<sensor_id>
Readings follow a sinusoidal pattern to simulate realistic sensor data.
"""

import paho.mqtt.client as mqtt
import time
import argparse
import math
import random
import json
import signal
import sys


class SensorAgent:
    def __init__(self, zone, sensor_type, sensor_id, broker='localhost', port=1883,
                 interval=2.0, base_value=20.0, amplitude=5.0, faulty=False):
        self.zone = zone
        self.sensor_type = sensor_type
        self.sensor_id = sensor_id
        self.broker = broker
        self.port = port
        self.interval = interval
        self.base_value = base_value
        self.amplitude = amplitude
        self.faulty = faulty
        self.running = True
        self.start_time = time.time()
        
        # Topic format: /<zone>/<type>/<sensor_id>
        self.topic = f"{zone}/{sensor_type}/{sensor_id}"
        
        # For reset functionality
        self.reset_topic = f"control/reset/{sensor_id}"
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=sensor_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Handle graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum=None, frame=None):
        print(f"[SENSOR] [{self.sensor_id}] Shutting down...")
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[SENSOR] [{self.sensor_id}] Connected! Publishing to: {self.topic}")
            # Subscribe to reset commands
            client.subscribe(self.reset_topic)
            print(f"[SENSOR] [{self.sensor_id}] Listening for reset on: {self.reset_topic}")
        else:
            print(f"[ERROR] [{self.sensor_id}] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle reset commands."""
        if msg.topic == self.reset_topic:
            print(f"[RESET] [{self.sensor_id}] Received reset command! Restarting...")
            self.faulty = False
            self.start_time = time.time()
            print(f"[SENSOR] [{self.sensor_id}] Sensor reset complete, now sending normal readings")
    
    def generate_reading(self):
        """Generate a sensor reading following a sinusoidal pattern."""
        elapsed = time.time() - self.start_time
        
        # Sinusoidal base value
        value = self.base_value + self.amplitude * math.sin(elapsed * 0.1)
        
        # Add small random noise
        value += random.uniform(-0.5, 0.5)
        
        # If faulty, occasionally send erroneous readings
        if self.faulty and random.random() < 0.3:
            # Send value significantly off (more than 2 std devs)
            value += random.choice([-1, 1]) * self.amplitude * 4
            print(f"[WARN] [{self.sensor_id}] Sending FAULTY reading!")
        
        return round(value, 2)
    
    def run(self):
        try:
            print(f"[SENSOR] [{self.sensor_id}] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            time.sleep(0.5)  # Wait for connection
            
            while self.running:
                reading = self.generate_reading()
                payload = json.dumps({
                    'sensor_id': self.sensor_id,
                    'zone': self.zone,
                    'type': self.sensor_type,
                    'value': reading,
                    'timestamp': time.time()
                })
                
                self.client.publish(self.topic, payload)
                print(f"[SENSOR] [{self.sensor_id}] Published: {reading} {self.sensor_type}")
                
                time.sleep(self.interval)
                
        except Exception as e:
            print(f"[ERROR] [{self.sensor_id}] Error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"[SENSOR] [{self.sensor_id}] Disconnected")


def main():
    parser = argparse.ArgumentParser(description='Sensor Agent')
    parser.add_argument('--zone', required=True, help='Zone/room name (e.g., living_room)')
    parser.add_argument('--type', dest='sensor_type', required=True, 
                        help='Sensor type (e.g., temperature, humidity)')
    parser.add_argument('--id', dest='sensor_id', required=True, help='Unique sensor ID')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--interval', type=float, default=2.0, help='Publishing interval (seconds)')
    parser.add_argument('--base', type=float, default=20.0, help='Base value for readings')
    parser.add_argument('--amplitude', type=float, default=5.0, help='Amplitude of variation')
    parser.add_argument('--faulty', action='store_true', help='Make sensor send faulty readings')
    args = parser.parse_args()
    
    sensor = SensorAgent(
        zone=args.zone,
        sensor_type=args.sensor_type,
        sensor_id=args.sensor_id,
        broker=args.broker,
        port=args.port,
        interval=args.interval,
        base_value=args.base,
        amplitude=args.amplitude,
        faulty=args.faulty
    )
    sensor.run()


if __name__ == "__main__":
    main()
