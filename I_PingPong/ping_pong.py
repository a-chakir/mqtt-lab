#!/usr/bin/env python3
"""
Ping-Pong MQTT Client - Part I.2
A single client configurable to play as ping or pong player.
Uses two topics for clean separation: game/ping and game/pong
"""

import paho.mqtt.client as mqtt
import time
import argparse
import sys


class PingPongClient:
    def __init__(self, mode, broker='localhost', port=1883, max_rounds=10):
        self.mode = mode.lower()
        self.broker = broker
        self.port = port
        self.max_rounds = max_rounds
        self.round_count = 0
        
        # Determine topics based on mode
        if self.mode == 'ping':
            self.listen_topic = 'game/pong'  # Listen for pong
            self.send_topic = 'game/ping'    # Send ping
            self.my_message = 'PING'
        else:
            self.listen_topic = 'game/ping'  # Listen for ping
            self.send_topic = 'game/pong'    # Send pong
            self.my_message = 'PONG'
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{mode}_player")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[GAME] [{self.mode.upper()}] Connected to broker!")
            client.subscribe(self.listen_topic)
            print(f"[GAME] [{self.mode.upper()}] Listening on: {self.listen_topic}")
            
            # Ping player starts the game
            if self.mode == 'ping':
                time.sleep(0.5)  # Small delay to ensure pong is ready
                self.send_message()
        else:
            print(f"[ERROR] [{self.mode.upper()}] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        received = msg.payload.decode()
        print(f"[RECV] [{self.mode.upper()}] Received: {received}")
        
        self.round_count += 1
        if self.round_count >= self.max_rounds:
            print(f"[WIN] [{self.mode.upper()}] Game finished after {self.max_rounds} rounds!")
            self.client.disconnect()
            return
        
        # Reply after a short delay
        time.sleep(0.5)
        self.send_message()
    
    def send_message(self):
        self.client.publish(self.send_topic, self.my_message)
        print(f"[SEND] [{self.mode.upper()}] Sent: {self.my_message}")
    
    def run(self):
        try:
            print(f"[GAME] [{self.mode.upper()}] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print(f"\n[STOP] [{self.mode.upper()}] Interrupted")
        except Exception as e:
            print(f"[ERROR] [{self.mode.upper()}] Error: {e}")
        finally:
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Ping-Pong MQTT Client')
    parser.add_argument('--mode', choices=['ping', 'pong'], required=True,
                        help='Play as ping or pong')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--rounds', type=int, default=10, help='Maximum rounds to play')
    args = parser.parse_args()
    
    client = PingPongClient(args.mode, args.broker, args.port, args.rounds)
    client.run()


if __name__ == "__main__":
    main()
