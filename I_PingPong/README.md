# Part I.2 - Ping-Pong Game

## Description
Two MQTT clients playing ping-pong. One responds "PING" to "PONG" messages, the other does the reverse.

## Topic Design
Uses **two topics** for clean separation:
- `game/ping` - Where PING messages are published
- `game/pong` - Where PONG messages are published

This design is cleaner than a single topic because each player only listens to the other's channel.

## Files
- `ping_pong.py` - Single client configurable to play as ping or pong
- `start_game.py` - Master process that spawns both players automatically

## Usage

### Automated (Recommended)
```bash
python start_game.py
```

### Manual (Two Terminals)
Terminal 1:
```bash
python ping_pong.py --mode pong
```

Terminal 2:
```bash
python ping_pong.py --mode ping
```

## Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--mode` | required | Play as 'ping' or 'pong' |
| `--broker` | localhost | MQTT broker address |
| `--port` | 1883 | MQTT broker port |
| `--rounds` | 10 | Maximum rounds to play |
