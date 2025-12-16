# Part II - Sensor Network

## Description
A dynamic sensor network simulation with:
- **Sensor agents** publishing readings at regular intervals
- **Averaging agents** computing averages over time windows
- **Interface agent** displaying a dashboard of results
- **Dynamic behavior** with agents joining/leaving the network

## Smart Home Theme
- **Zones**: living_room, bedroom, kitchen, bathroom
- **Sensor Types**: temperature (°C), humidity (%)

## Topic Structure
```
Sensor readings:   /<zone>/<type>/<sensor_id>
Averages:          averages/<zone>/<type>
Reset commands:    control/reset/<sensor_id>
Alerts:            alerts/<type>
```

## Files
| File | Description |
|------|-------------|
| `sensor.py` | Sensor agent with sinusoidal readings |
| `averaging.py` | Computes averages over time windows |
| `interface.py` | Dashboard displaying network state |
| `master.py` | Orchestrates the network dynamically |

## Quick Start
```bash
# Automated simulation (recommended)
python master.py --duration 120

# View interface separately
python interface.py
```

## Manual Mode

### Start Individual Sensors
```bash
python sensor.py --zone living_room --type temperature --id sensor_001
python sensor.py --zone living_room --type humidity --id sensor_002 --faulty
```

### Start Averaging Agents
```bash
python averaging.py --zone living_room --type temperature
```

### Start Interface
```bash
python interface.py
```

## Parameters

### sensor.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--zone` | required | Zone name |
| `--type` | required | Sensor type |
| `--id` | required | Unique sensor ID |
| `--interval` | 2.0 | Publishing interval (seconds) |
| `--base` | 20.0 | Base value for readings |
| `--amplitude` | 5.0 | Amplitude of sinusoidal variation |
| `--faulty` | false | Send erroneous readings |

### averaging.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--zone` | required | Zone to monitor |
| `--type` | required | Sensor type to monitor |
| `--window` | 10 | Time window in seconds |
| `--interval` | 5 | Publish interval in seconds |

### master.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--duration` | 120 | Simulation duration in seconds |
