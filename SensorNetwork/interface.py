#!/usr/bin/env python3
"""
Interface Agent - Part II.1
Displays averages grouped by zone and measurement types.
Can display in console or with a simple GUI.
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
from collections import defaultdict
from datetime import datetime
import os


class InterfaceAgent:
    def __init__(self, broker='localhost', port=1883, refresh_interval=3):
        self.broker = broker
        self.port = port
        self.refresh_interval = refresh_interval
        self.running = True
        
        # Store latest averages: zone -> type -> data
        self.averages = defaultdict(lambda: defaultdict(dict))
        
        # Also monitor raw sensor topics for alerts
        self.alerts = []
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id="interface_agent")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[INTERFACE] Connected to broker!")
            # Subscribe to all averages
            client.subscribe("averages/#")
            # Subscribe to alerts
            client.subscribe("alerts/#")
            print("[INTERFACE] Subscribed to averages/# and alerts/#")
        else:
            print(f"[ERROR] [INTERFACE] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            
            if msg.topic.startswith("averages/"):
                zone = data.get('zone', 'unknown')
                sensor_type = data.get('type', 'unknown')
                self.averages[zone][sensor_type] = {
                    'average': data.get('average', 0),
                    'std_dev': data.get('std_dev', 0),
                    'sensor_count': data.get('sensor_count', 0),
                    'sample_count': data.get('sample_count', 0),
                    'timestamp': data.get('timestamp', time.time())
                }
            
            elif msg.topic.startswith("alerts/"):
                self.alerts.append({
                    'message': data.get('message', str(data)),
                    'timestamp': time.time()
                })
                # Keep only last 5 alerts
                self.alerts = self.alerts[-5:]
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ERROR] [INTERFACE] Error parsing: {e}")
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display(self):
        """Display the current state of the sensor network."""
        self.clear_screen()
        
        print("=" * 60)
        print("        SMART HOME SENSOR NETWORK DASHBOARD")
        print("=" * 60)
        print(f"  Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.averages:
            print("\n  [WAIT] Waiting for sensor data...\n")
        else:
            for zone in sorted(self.averages.keys()):
                print(f"\n  [ZONE] {zone.upper().replace('_', ' ')}")
                print("  " + "-" * 40)
                
                for sensor_type in sorted(self.averages[zone].keys()):
                    data = self.averages[zone][sensor_type]
                    avg = data['average']
                    std = data['std_dev']
                    sensors = data['sensor_count']
                    
                    # Choose unit based on type
                    units = {
                        'temperature': 'C',
                        'humidity': '%',
                        'pressure': 'hPa',
                        'light': 'lux',
                        'motion': ''
                    }
                    unit = units.get(sensor_type, '')
                    
                    print(f"    {sensor_type.capitalize()}: {avg:.1f}{unit} "
                          f"(std={std:.2f}, {sensors} sensor(s))")
        
        # Display alerts
        if self.alerts:
            print("\n" + "=" * 60)
            print("  [ALERTS] RECENT ALERTS")
            print("  " + "-" * 40)
            for alert in self.alerts[-5:]:
                dt = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
                print(f"    [{dt}] {alert['message'][:50]}")
        
        print("\n" + "=" * 60)
        print("  Press Ctrl+C to exit")
        print("=" * 60)
    
    def run(self):
        try:
            print(f"[INTERFACE] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            time.sleep(1)
            
            while self.running:
                self.display()
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n[STOP] [INTERFACE] Shutting down...")
        except Exception as e:
            print(f"[ERROR] [INTERFACE] Error: {e}")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Interface Agent')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--refresh', type=int, default=3, help='Refresh interval in seconds')
    args = parser.parse_args()
    
    agent = InterfaceAgent(
        broker=args.broker,
        port=args.port,
        refresh_interval=args.refresh
    )
    agent.run()


if __name__ == "__main__":
    main()
