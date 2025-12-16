#!/usr/bin/env python3
"""
Detection Agent - Part II.3
Monitors sensor readings and publishes alerts when anomalies are detected.
An anomaly is a value more than 2 standard deviations from the average.
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
import statistics
from collections import defaultdict
import threading


class DetectionAgent:
    def __init__(self, broker='localhost', port=1883, window_seconds=30):
        self.broker = broker
        self.port = port
        self.window_seconds = window_seconds
        self.running = True
        
        # Store readings per zone/type: zone -> type -> [(timestamp, value, sensor_id), ...]
        self.readings = defaultdict(lambda: defaultdict(list))
        # Store computed stats
        self.stats = defaultdict(lambda: defaultdict(dict))
        self.lock = threading.Lock()
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id="detection_agent")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[DETECTION] Connected to broker!")
            # Subscribe to all sensor readings using wildcard
            client.subscribe("+/+/+")  # zone/type/sensor_id
            # Also subscribe to averages for reference
            client.subscribe("averages/#")
            print("[DETECTION] Monitoring all sensor readings...")
        else:
            print(f"[ERROR] [DETECTION] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split('/')
        
        # Skip non-sensor topics
        if topic_parts[0] in ['averages', 'alerts', 'control', 'cfp', 'bids', 'awards', 'rejects']:
            if topic_parts[0] == 'averages':
                self.handle_average(msg)
            return
        
        try:
            data = json.loads(msg.payload.decode())
            
            # Extract info from topic: zone/type/sensor_id
            if len(topic_parts) >= 3:
                zone = topic_parts[0]
                sensor_type = topic_parts[1]
                sensor_id = topic_parts[2]
                value = data.get('value', 0)
                timestamp = data.get('timestamp', time.time())
                
                with self.lock:
                    self.readings[zone][sensor_type].append((timestamp, value, sensor_id))
                
                # Check for anomaly
                self.check_anomaly(zone, sensor_type, sensor_id, value)
                
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            pass  # Ignore malformed messages
    
    def handle_average(self, msg):
        """Store averages from averaging agents for reference."""
        try:
            data = json.loads(msg.payload.decode())
            zone = data.get('zone')
            sensor_type = data.get('type')
            
            if zone and sensor_type:
                with self.lock:
                    self.stats[zone][sensor_type] = {
                        'average': data.get('average', 0),
                        'std_dev': data.get('std_dev', 1)
                    }
        except:
            pass
    
    def compute_stats(self, zone, sensor_type):
        """Compute mean and std_dev from recent readings."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        with self.lock:
            readings = self.readings[zone][sensor_type]
            # Filter to recent readings
            valid = [(t, v, s) for t, v, s in readings if t >= cutoff_time]
            self.readings[zone][sensor_type] = valid  # Clean old
            
            if len(valid) >= 5:  # Need enough samples
                values = [v for _, v, _ in valid]
                return {
                    'average': statistics.mean(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 1
                }
            
            # Fall back to stats from averaging agent
            if zone in self.stats and sensor_type in self.stats[zone]:
                return self.stats[zone][sensor_type]
        
        return None
    
    def check_anomaly(self, zone, sensor_type, sensor_id, value):
        """Check if a reading is anomalous (> 2 std devs from mean)."""
        stats = self.compute_stats(zone, sensor_type)
        
        if stats is None:
            return  # Not enough data
        
        avg = stats['average']
        std = stats['std_dev']
        
        if std == 0:
            std = 1  # Avoid division by zero
        
        # Calculate z-score
        z_score = abs(value - avg) / std
        
        if z_score > 2:
            self.publish_alert(zone, sensor_type, sensor_id, value, avg, std, z_score)
    
    def publish_alert(self, zone, sensor_type, sensor_id, value, avg, std, z_score):
        """Publish an alert about a detected anomaly."""
        alert = {
            'type': 'anomaly',
            'zone': zone,
            'sensor_type': sensor_type,
            'sensor_id': sensor_id,
            'value': value,
            'expected_avg': round(avg, 2),
            'std_dev': round(std, 2),
            'z_score': round(z_score, 2),
            'message': f"Anomaly detected: {sensor_id} in {zone} reported {value:.2f} "
                       f"(expected ~{avg:.2f}, z={z_score:.2f})",
            'timestamp': time.time()
        }
        
        self.client.publish(f"alerts/anomaly/{sensor_id}", json.dumps(alert))
        
        print(f"[ALERT] {sensor_id} reported {value:.2f} "
              f"(avg={avg:.2f}, std={std:.2f}, z={z_score:.2f})")
    
    def run(self):
        try:
            print(f"[DETECTION] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n[STOP] [DETECTION] Shutting down...")
        except Exception as e:
            print(f"[ERROR] [DETECTION] Error: {e}")
        finally:
            self.running = False
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Detection Agent')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--window', type=int, default=30, help='Time window for stats (seconds)')
    args = parser.parse_args()
    
    agent = DetectionAgent(
        broker=args.broker,
        port=args.port,
        window_seconds=args.window
    )
    agent.run()


if __name__ == "__main__":
    main()
