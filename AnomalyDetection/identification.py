#!/usr/bin/env python3
"""
Identification Agent - Part II.3
Monitors alerts and sends reset commands to faulty sensors.
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
from collections import defaultdict


class IdentificationAgent:
    def __init__(self, broker='localhost', port=1883, alert_threshold=3):
        self.broker = broker
        self.port = port
        self.alert_threshold = alert_threshold  # Number of alerts before reset
        self.running = True
        
        # Track alerts per sensor
        self.alert_counts = defaultdict(int)
        self.recently_reset = set()  # Avoid spamming resets
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id="identification_agent")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[IDENTIFICATION] Connected to broker!")
            # Subscribe to all alerts
            client.subscribe("alerts/#")
            print("[IDENTIFICATION] Monitoring alerts...")
        else:
            print(f"[ERROR] [IDENTIFICATION] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            
            if data.get('type') == 'anomaly':
                sensor_id = data.get('sensor_id')
                
                if sensor_id and sensor_id not in self.recently_reset:
                    self.alert_counts[sensor_id] += 1
                    
                    print(f"[IDENTIFICATION] Alert count for {sensor_id}: "
                          f"{self.alert_counts[sensor_id]}/{self.alert_threshold}")
                    
                    if self.alert_counts[sensor_id] >= self.alert_threshold:
                        self.reset_sensor(sensor_id)
                        
        except (json.JSONDecodeError, KeyError) as e:
            pass
    
    def reset_sensor(self, sensor_id):
        """Send reset command to a faulty sensor."""
        reset_topic = f"control/reset/{sensor_id}"
        reset_command = json.dumps({
            'command': 'reset',
            'sensor_id': sensor_id,
            'reason': 'Anomalous readings detected',
            'timestamp': time.time()
        })
        
        self.client.publish(reset_topic, reset_command)
        print(f"[RESET] Sent RESET command to: {sensor_id}")
        
        # Mark as recently reset
        self.recently_reset.add(sensor_id)
        self.alert_counts[sensor_id] = 0
        
        # Clear recently reset after 30 seconds
        def clear_reset():
            time.sleep(30)
            self.recently_reset.discard(sensor_id)
        
        import threading
        threading.Thread(target=clear_reset, daemon=True).start()
    
    def run(self):
        try:
            print(f"[IDENTIFICATION] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n[STOP] [IDENTIFICATION] Shutting down...")
        except Exception as e:
            print(f"[ERROR] [IDENTIFICATION] Error: {e}")
        finally:
            self.running = False
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Identification Agent')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--threshold', type=int, default=3, 
                        help='Number of alerts before sending reset')
    args = parser.parse_args()
    
    agent = IdentificationAgent(
        broker=args.broker,
        port=args.port,
        alert_threshold=args.threshold
    )
    agent.run()


if __name__ == "__main__":
    main()
