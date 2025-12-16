#!/usr/bin/env python3
"""
Contract Net Simulation Runner - Part III.1
Starts supervisor and multiple machines for the Contract Net protocol demonstration.
"""

import subprocess
import sys
import os
import time
import signal
import threading


class ContractNetSimulation:
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.processes = []
        self.running = True
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum=None, frame=None):
        print("\n[STOP] Shutting down simulation...")
        self.running = False
        self.stop_all()
    
    def spawn(self, script, args=None, capture_output=True):
        """Spawn a process."""
        cmd = [sys.executable, os.path.join(self.script_dir, script)]
        if args:
            cmd.extend(args)
        
        if capture_output:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
        else:
            process = subprocess.Popen(
                cmd,
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
    
    def read_output(self, process, name):
        """Read and print output from a process."""
        try:
            for line in process.stdout:
                if line.strip():
                    print(f"[{name:12}] {line}", end='')
        except:
            pass
    
    def run(self, num_machines=4, num_jobs=10):
        print("=" * 70)
        print("     CONTRACT NET PROTOCOL SIMULATION")
        print("=" * 70)
        
        # Define machine configurations
        # Each machine has different capabilities and speeds
        machine_configs = [
            {'id': 'machine_A', 'caps': ['assembly:4', 'inspection:2']},
            {'id': 'machine_B', 'caps': ['assembly:6', 'welding:8', 'inspection:3']},
            {'id': 'machine_C', 'caps': ['welding:5', 'painting:4']},
            {'id': 'machine_D', 'caps': ['painting:3', 'packaging:2', 'inspection:4']},
            {'id': 'machine_E', 'caps': ['assembly:5', 'welding:6', 'painting:5', 'packaging:3']},
        ]
        
        # Start machines
        print("\n[SETUP] Starting machines...")
        threads = []
        
        for i, config in enumerate(machine_configs[:num_machines]):
            print(f"   Starting {config['id']} with capabilities: {config['caps']}")
            process = self.spawn('machine.py', [
                '--id', config['id'],
                '--broker', self.broker,
                '--port', str(self.port),
                '--capabilities'] + config['caps']
            )
            
            # Thread to read output
            t = threading.Thread(
                target=self.read_output, 
                args=(process, config['id']),
                daemon=True
            )
            t.start()
            threads.append(t)
            time.sleep(0.3)
        
        print("\n[WAIT] Waiting for machines to be ready...")
        time.sleep(2)
        
        # Start supervisor
        print("\n[SETUP] Starting supervisor...")
        supervisor = self.spawn('supervisor.py', [
            '--broker', self.broker,
            '--port', str(self.port),
            '--jobs', str(num_jobs),
            '--deadline', '3',
            '--interval', '2'
        ])
        
        supervisor_thread = threading.Thread(
            target=self.read_output,
            args=(supervisor, 'SUPERVISOR'),
            daemon=True
        )
        supervisor_thread.start()
        
        print("\n" + "=" * 70)
        print("     Simulation running... Press Ctrl+C to stop")
        print("=" * 70 + "\n")
        
        # Wait for supervisor to finish or interrupt
        try:
            supervisor.wait()
        except:
            pass
        
        print("\n[WAIT] Allowing jobs to complete...")
        time.sleep(5)
        
        self.shutdown()
        print("\n[DONE] Simulation complete!")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Contract Net Simulation')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--machines', type=int, default=4, help='Number of machines')
    parser.add_argument('--jobs', type=int, default=10, help='Number of jobs')
    args = parser.parse_args()
    
    sim = ContractNetSimulation(broker=args.broker, port=args.port)
    sim.run(num_machines=args.machines, num_jobs=args.jobs)


if __name__ == "__main__":
    main()
