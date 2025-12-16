#!/usr/bin/env python3
"""
Master Process - Part II.2
Orchestrates the sensor network by spawning and managing agents dynamically.
Demonstrates dynamic agent entry/exit from the system.
"""

import subprocess
import sys
import os
import time
import random
import signal
import threading


class NetworkMaster:
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.processes = {}  # id -> process
        self.running = True
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Configuration for smart home
        self.zones = ['living_room', 'bedroom', 'kitchen', 'bathroom']
        self.sensor_types = {
            'temperature': {'base': 22.0, 'amplitude': 3.0},
            'humidity': {'base': 50.0, 'amplitude': 10.0}
        }
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum=None, frame=None):
        print("\n[MASTER] Shutting down all agents...")
        self.running = False
        self.stop_all()
    
    def spawn_sensor(self, zone, sensor_type, sensor_id, faulty=False):
        """Spawn a new sensor agent."""
        config = self.sensor_types[sensor_type]
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, 'sensor.py'),
            '--zone', zone,
            '--type', sensor_type,
            '--id', sensor_id,
            '--broker', self.broker,
            '--port', str(self.port),
            '--base', str(config['base']),
            '--amplitude', str(config['amplitude']),
            '--interval', '2'
        ]
        
        if faulty:
            cmd.append('--faulty')
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        self.processes[sensor_id] = {
            'process': process,
            'type': 'sensor',
            'zone': zone,
            'sensor_type': sensor_type
        }
        print(f"[START] Spawned sensor: {sensor_id} ({zone}/{sensor_type})")
        return sensor_id
    
    def spawn_averaging_agent(self, zone, sensor_type):
        """Spawn an averaging agent."""
        agent_id = f"avg_{zone}_{sensor_type}"
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, 'averaging.py'),
            '--zone', zone,
            '--type', sensor_type,
            '--broker', self.broker,
            '--port', str(self.port),
            '--window', '10',
            '--interval', '5'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        self.processes[agent_id] = {
            'process': process,
            'type': 'averaging',
            'zone': zone,
            'sensor_type': sensor_type
        }
        print(f"[START] Spawned averaging agent: {agent_id}")
        return agent_id
    
    def spawn_interface(self):
        """Spawn the interface agent."""
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, 'interface.py'),
            '--broker', self.broker,
            '--port', str(self.port),
            '--refresh', '3'
        ]
        
        process = subprocess.Popen(
            cmd,
            # Don't capture output for interface - let it display
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        self.processes['interface'] = {
            'process': process,
            'type': 'interface'
        }
        print("[START] Spawned interface agent")
    
    def stop_agent(self, agent_id):
        """Stop a specific agent."""
        if agent_id in self.processes:
            proc_info = self.processes[agent_id]
            proc_info['process'].terminate()
            proc_info['process'].wait(timeout=5)
            del self.processes[agent_id]
            print(f"[STOP] Stopped agent: {agent_id}")
    
    def stop_all(self):
        """Stop all agents."""
        for agent_id in list(self.processes.keys()):
            try:
                self.processes[agent_id]['process'].terminate()
            except:
                pass
        
        time.sleep(1)
        
        for agent_id in list(self.processes.keys()):
            try:
                self.processes[agent_id]['process'].kill()
            except:
                pass
        
        self.processes.clear()
        print("[STOP] All agents stopped")
    
    def run_dynamic_simulation(self, duration=120):
        """Run a simulation with dynamic agent spawning/killing."""
        print("=" * 60)
        print("     SMART HOME SENSOR NETWORK SIMULATION")
        print("=" * 60)
        
        # Initial setup: spawn sensors and averaging agents
        sensor_counter = 0
        
        # Spawn initial sensors (2 per zone per type)
        for zone in self.zones[:2]:  # Start with 2 zones
            for sensor_type in self.sensor_types:
                for i in range(2):
                    sensor_counter += 1
                    self.spawn_sensor(zone, sensor_type, f"sensor_{sensor_counter:03d}")
                    time.sleep(0.3)
                
                # Spawn averaging agent for this zone/type
                self.spawn_averaging_agent(zone, sensor_type)
                time.sleep(0.2)
        
        print("\n[MASTER] Initial setup complete. Starting dynamic simulation...")
        print("   Agents will be spawned/killed dynamically")
        print("   Press Ctrl+C to stop\n")
        
        time.sleep(5)
        
        # Dynamic phase: randomly add/remove sensors
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            time.sleep(10)  # Every 10 seconds
            
            if not self.running:
                break
            
            action = random.choice(['add', 'remove', 'add', 'nothing'])  # Bias towards adding
            
            if action == 'add':
                zone = random.choice(self.zones)
                sensor_type = random.choice(list(self.sensor_types.keys()))
                sensor_counter += 1
                # 10% chance to spawn a faulty sensor
                faulty = random.random() < 0.1
                self.spawn_sensor(zone, sensor_type, f"sensor_{sensor_counter:03d}", faulty=faulty)
                
                # Ensure there's an averaging agent for this zone/type
                avg_id = f"avg_{zone}_{sensor_type}"
                if avg_id not in self.processes:
                    self.spawn_averaging_agent(zone, sensor_type)
            
            elif action == 'remove':
                # Find a sensor to remove (not the last one)
                sensors = [k for k, v in self.processes.items() 
                          if v['type'] == 'sensor']
                if len(sensors) > 4:  # Keep at least 4 sensors
                    victim = random.choice(sensors)
                    self.stop_agent(victim)
        
        self.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sensor Network Master')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--duration', type=int, default=120, help='Simulation duration (seconds)')
    args = parser.parse_args()
    
    master = NetworkMaster(broker=args.broker, port=args.port)
    master.run_dynamic_simulation(duration=args.duration)


if __name__ == "__main__":
    main()
