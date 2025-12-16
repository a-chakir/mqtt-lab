#!/usr/bin/env python3
"""
Averaging Agent - Part II.1
Collects readings from sensors and computes averages over a time window.
Publishes averages on dedicated topics.
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
import statistics
import threading
from collections import defaultdict


class AveragingAgent:
    def __init__(self, zone, sensor_type, broker='localhost', port=1883,
                 window_seconds=10, publish_interval=5):
        self.zone = zone
        self.sensor_type = sensor_type
        self.broker = broker
        self.port = port
        self.window_seconds = window_seconds
        self.publish_interval = publish_interval
        self.running = True
        
        # Subscribe to all sensors in this zone/type
        self.subscribe_topic = f"{zone}/{sensor_type}/+"
        
        # Publish averages on dedicated topic
        self.publish_topic = f"averages/{zone}/{sensor_type}"
        
        # Store readings with timestamps
        self.readings = defaultdict(list)  # sensor_id -> [(timestamp, value), ...]
        self.lock = threading.Lock()
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id=f"avg_{zone}_{sensor_type}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[AVG] [{self.zone}-{self.sensor_type}] Connected!")
            client.subscribe(self.subscribe_topic)
            print(f"[AVG] Subscribed to: {self.subscribe_topic}")
        else:
            print(f"[ERROR] [AVG] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Collect sensor readings."""
        try:
            data = json.loads(msg.payload.decode())
            sensor_id = data.get('sensor_id', msg.topic.split('/')[-1])
            value = data['value']
            timestamp = data.get('timestamp', time.time())
            
            with self.lock:
                self.readings[sensor_id].append((timestamp, value))
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ERROR] [AVG] Error parsing message: {e}")
    
    def compute_and_publish_average(self):
        """Compute average over the time window and publish."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        all_values = []
        sensor_count = 0
        
        with self.lock:
            for sensor_id, sensor_readings in self.readings.items():
                # Filter readings within the time window
                valid_readings = [(t, v) for t, v in sensor_readings if t >= cutoff_time]
                self.readings[sensor_id] = valid_readings  # Clean old readings
                
                if valid_readings:
                    sensor_count += 1
                    all_values.extend([v for _, v in valid_readings])
        
        if all_values:
            avg = statistics.mean(all_values)
            std_dev = statistics.stdev(all_values) if len(all_values) > 1 else 0
            
            payload = json.dumps({
                'zone': self.zone,
                'type': self.sensor_type,
                'average': round(avg, 2),
                'std_dev': round(std_dev, 2),
                'sensor_count': sensor_count,
                'sample_count': len(all_values),
                'window_seconds': self.window_seconds,
                'timestamp': current_time
            })
            
            self.client.publish(self.publish_topic, payload)
            print(f"[AVG] [{self.zone}-{self.sensor_type}] Average: {avg:.2f} (std={std_dev:.2f}, n={len(all_values)})")
        else:
            print(f"[AVG] [{self.zone}-{self.sensor_type}] No readings in window")
    
    def run(self):
        try:
            print(f"[AVG] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            time.sleep(0.5)
            
            while self.running:
                self.compute_and_publish_average()
                time.sleep(self.publish_interval)
                
        except KeyboardInterrupt:
            print("\n[STOP] [AVG] Interrupted")
        except Exception as e:
            print(f"[ERROR] [AVG] Error: {e}")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            print("[AVG] Disconnected")


def main():
    parser = argparse.ArgumentParser(description='Averaging Agent')
    parser.add_argument('--zone', required=True, help='Zone to monitor')
    parser.add_argument('--type', dest='sensor_type', required=True, 
                        help='Sensor type to monitor')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--window', type=int, default=10, help='Time window in seconds')
    parser.add_argument('--interval', type=int, default=5, help='Publish interval in seconds')
    args = parser.parse_args()
    
    agent = AveragingAgent(
        zone=args.zone,
        sensor_type=args.sensor_type,
        broker=args.broker,
        port=args.port,
        window_seconds=args.window,
        publish_interval=args.interval
    )
    agent.run()


if __name__ == "__main__":
    main()
