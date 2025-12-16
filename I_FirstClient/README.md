# Part I.1 - First MQTT Client

## Description
A simple MQTT client that connects to a broker, subscribes to a topic, and publishes messages with delays.

## Usage
```bash
python first_client.py [--broker HOST] [--port PORT] [--topic TOPIC] [--messages N] [--delay SECONDS]
```

## Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--broker` | localhost | MQTT broker address |
| `--port` | 1883 | MQTT broker port |
| `--topic` | hello | Topic to subscribe and publish to |
| `--messages` | 5 | Number of messages to publish |
| `--delay` | 2.0 | Delay between messages (seconds) |

## Example
```bash
python first_client.py --topic "test/hello" --messages 3 --delay 1.5
```
