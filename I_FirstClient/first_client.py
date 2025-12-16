#!/usr/bin/env python3
"""
First MQTT Client - Part I.1
Connects to broker, subscribes to a topic, and publishes messages.
"""

import paho.mqtt.client as mqtt
import time
import argparse


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when connected to broker."""
    if rc == 0:
        print(f"[OK] Connected to MQTT Broker successfully!")
        # Subscribe to the topic upon connection
        client.subscribe(userdata['topic'])
        print(f"[OK] Subscribed to topic: {userdata['topic']}")
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    """Callback when a message is received."""
    print(f"[RECV] Received: '{msg.payload.decode()}' on topic '{msg.topic}'")


def on_publish(client, userdata, mid, properties=None, reason_code=None):
    """Callback when a message is published."""
    print(f"[PUB] Message {mid} published successfully")


def main():
    parser = argparse.ArgumentParser(description='First MQTT Client')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='hello', help='Topic to subscribe/publish')
    parser.add_argument('--messages', type=int, default=5, help='Number of messages to send')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between messages (seconds)')
    args = parser.parse_args()

    # Create client with userdata for callbacks
    userdata = {'topic': args.topic}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=userdata)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    print(f"Connecting to broker at {args.broker}:{args.port}...")
    
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(1)
        
        # Publish several messages with delays
        for i in range(1, args.messages + 1):
            message = f"Hello MQTT! Message #{i}"
            result = client.publish(args.topic, message)
            print(f"[SEND] Publishing: '{message}'")
            time.sleep(args.delay)
        
        # Keep listening for a bit to receive any messages
        print("\n[WAIT] Listening for messages for 5 more seconds...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[DONE] Disconnected from broker")


if __name__ == "__main__":
    main()
