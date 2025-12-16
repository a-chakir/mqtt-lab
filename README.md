# MQTT Multi-Agent Systems Lab

A complete implementation of the MQTT lab for the Multi-Agent Systems course (ESISAR 5A IR&C - CS534).

## Prerequisites

- Python 3.8+
- MQTT Broker (Mosquitto, shiftr.io, or any other)

## Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install paho-mqtt
```

## Project Structure

```
mqtt/
├── I_FirstClient/          # Part I.1 - First MQTT Client
│   ├── first_client.py     # Connect, subscribe, publish
│   └── README.md
│
├── I_PingPong/             # Part I.2 - Ping-Pong Game
│   ├── ping_pong.py        # Configurable ping/pong agent
│   ├── start_game.py       # Auto-start both players
│   └── README.md
│
├── SensorNetwork/          # Part II.1-2 - Sensor Network
│   ├── sensor.py           # Sensor agent (sinusoidal readings)
│   ├── averaging.py        # Averaging agent
│   ├── interface.py        # Dashboard display
│   ├── master.py           # Dynamic simulation orchestrator
│   └── README.md
│
├── AnomalyDetection/       # Part II.3 - Anomaly Detection
│   ├── detection.py        # Detect anomalies (>2σ)
│   ├── identification.py   # Reset faulty sensors
│   ├── master.py           # Simulation orchestrator
│   └── README.md
│
└── ContractNet/            # Part III - Contract Net Protocol
    ├── supervisor.py       # Job dispatcher (CfP, bids, awards)
    ├── machine.py          # Worker machine agent
    ├── run_simulation.py   # Simulation runner
    └── README.md
```

## Quick Start

### Part I.1 - First Client
```bash
cd I_FirstClient
python first_client.py --topic hello --messages 5
```

### Part I.2 - Ping-Pong
```bash
cd I_PingPong
python start_game.py
```

### Part II - Sensor Network
```bash
cd SensorNetwork
python master.py --duration 120
```

### Part II.3 - Anomaly Detection
```bash
cd AnomalyDetection
python master.py --duration 120
```

### Part III - Contract Net
```bash
cd ContractNet
python run_simulation.py --machines 4 --jobs 10
```

## Design Choices

### Programming Language: Python
- Excellent MQTT library (paho-mqtt)
- Quick prototyping for multi-agent systems
- Good threading support for concurrent agents

### Topic Design
- **Sensor Network**: `/<zone>/<type>/<sensor_id>` for hierarchical organization
- **Contract Net**: Separate topics for CfP, bids, awards, and rejections

### Threading vs Multiprocessing
- Each agent runs in its own process (spawned by master)
- Internal async operations use threading
- Clean separation, easy to monitor, realistic distribution

### Message Format
- All messages use JSON for flexibility and debugging
- Each message includes timestamp and sender ID

## Author
CHAKIR Abderrahmane
abderrahmane.chakir@etu.esisar.grenoble-inp.fr
