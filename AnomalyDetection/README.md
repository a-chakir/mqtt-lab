# Part II.3 - Anomaly Detection

## Description
Extension to the sensor network that detects anomalous readings and resets faulty sensors.

## Components
- **Detection Agent**: Monitors all sensor readings, alerts when values > 2σ from mean
- **Identification Agent**: Tracks alerts, sends reset commands after threshold
- **Sensor Reset**: Sensors listen for reset commands and resume normal operation

## How It Works
1. Detection agent calculates rolling statistics for each zone/type
2. When a reading is > 2 standard deviations from the mean, an alert is published
3. Identification agent counts alerts per sensor
4. After 3 alerts, a reset command is sent to the faulty sensor
5. Sensor receives reset, clears faulty state, resumes normal operation

## Topic Structure
```
Alerts:          alerts/anomaly/<sensor_id>
Reset commands:  control/reset/<sensor_id>
```

## Quick Start
```bash
# Run complete simulation
python master.py --duration 120
```

## Manual Mode
```bash
# Terminal 1: Detection agent
python detection.py

# Terminal 2: Identification agent  
python identification.py --threshold 3

# Terminal 3+: Run sensors from SensorNetwork folder
python ../SensorNetwork/sensor.py --zone living_room --type temperature --id sensor_001
python ../SensorNetwork/sensor.py --zone living_room --type temperature --id sensor_faulty --faulty
```

## Parameters

### detection.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--window` | 30 | Time window for computing statistics |

### identification.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--threshold` | 3 | Number of alerts before sending reset |
