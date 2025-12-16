#!/usr/bin/env python3
"""
Anomaly Detection Master - Part II.3
Runs the complete anomaly detection simulation.
"""

import subprocess
import sys
import os
import time
import signal


class AnomalyMaster:
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.processes = []
        self.running = True
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sensor_dir = os.path.join(os.path.dirname(self.script_dir), 'SensorNetwork')
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum=None, frame=None):
        print("\n[MASTER] Shutting down...")
        self.running = False
        self.stop_all()
    
    def spawn(self, script_path, args=None):
        """Spawn a process."""
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        self.processes.append(process)
        return process
    
    def stop_all(self):
        for p in self.processes:
            try:
                p.terminate()
            except:
                pass
        time.sleep(1)
        for p in self.processes:
            try:
                p.kill()
            except:
                pass
        print("[STOP] All processes stopped")
    
    def run(self, duration=120):
        print("=" * 60)
        print("    ANOMALY DETECTION SIMULATION")
        print("=" * 60)
        
        # Spawn normal sensors
        print("\n[SENSOR] Spawning normal sensors...")
        for i in range(1, 4):
            self.spawn(os.path.join(self.sensor_dir, 'sensor.py'), [
                '--zone', 'living_room', '--type', 'temperature',
                '--id', f'sensor_{i:03d}', '--broker', self.broker
            ])
            time.sleep(0.3)
        
        # Spawn one faulty sensor
        print("[WARN] Spawning FAULTY sensor...")
        self.spawn(os.path.join(self.sensor_dir, 'sensor.py'), [
            '--zone', 'living_room', '--type', 'temperature',
            '--id', 'sensor_faulty', '--broker', self.broker, '--faulty'
        ])
        
        time.sleep(1)
        
        # Spawn averaging agent
        print("[AVG] Spawning averaging agent...")
        self.spawn(os.path.join(self.sensor_dir, 'averaging.py'), [
            '--zone', 'living_room', '--type', 'temperature',
            '--broker', self.broker
        ])
        
        time.sleep(1)
        
        # Spawn detection agent
        print("[DETECTION] Spawning detection agent...")
        self.spawn(os.path.join(self.script_dir, 'detection.py'), [
            '--broker', self.broker, '--window', '30'
        ])
        
        time.sleep(1)
        
        # Spawn identification agent
        print("[IDENTIFICATION] Spawning identification agent...")
        self.spawn(os.path.join(self.script_dir, 'identification.py'), [
            '--broker', self.broker, '--threshold', '3'
        ])
        
        print("\n" + "=" * 60)
        print("[RUN] Simulation running... Press Ctrl+C to stop")
        print("   Watch for anomaly alerts and reset commands!")
        print("=" * 60 + "\n")
        
        # Read output from processes
        import threading
        
        def read_output(process, name):
            try:
                for line in process.stdout:
                    if line.strip():
                        print(f"[{name}] {line}", end='')
            except:
                pass
        
        threads = []
        names = ['sensor_001', 'sensor_002', 'sensor_003', 'FAULTY', 
                 'AVERAGING', 'DETECTION', 'IDENTIFICATION']
        
        for p, name in zip(self.processes, names):
            t = threading.Thread(target=read_output, args=(p, name), daemon=True)
            t.start()
            threads.append(t)
        
        # Wait for duration
        start = time.time()
        while self.running and (time.time() - start) < duration:
            time.sleep(1)
        
        self.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Anomaly Detection Master')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--duration', type=int, default=120, help='Simulation duration')
    args = parser.parse_args()
    
    master = AnomalyMaster(broker=args.broker, port=args.port)
    master.run(duration=args.duration)


if __name__ == "__main__":
    main()
