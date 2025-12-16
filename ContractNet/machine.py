#!/usr/bin/env python3
"""
Machine Agent - Part III.1
Implements the Contract Net protocol machine/worker:
- Listens for CfP
- Submits bids or rejections
- Executes awarded jobs
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
import threading
import random


class MachineAgent:
    def __init__(self, machine_id, capabilities, broker='localhost', port=1883):
        self.machine_id = machine_id
        self.broker = broker
        self.port = port
        self.running = True
        
        # Machine capabilities: job_type -> time_to_complete
        self.capabilities = capabilities
        
        # Current state
        self.busy = False
        self.current_job = None
        self.job_end_time = None
        
        # Statistics
        self.jobs_completed = 0
        self.bids_submitted = 0
        self.bids_won = 0
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id=machine_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[MACHINE] [{self.machine_id}] Connected! Capabilities: {list(self.capabilities.keys())}")
            # Subscribe to CfP
            client.subscribe("cfp/jobs")
            # Subscribe to awards for this machine
            client.subscribe(f"awards/{self.machine_id}")
            # Subscribe to rejections for this machine
            client.subscribe(f"rejects/{self.machine_id}")
            print(f"[MACHINE] [{self.machine_id}] Ready to receive CfPs")
        else:
            print(f"[ERROR] [{self.machine_id}] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            
            if msg.topic == "cfp/jobs":
                self.handle_cfp(data)
            
            elif msg.topic == f"awards/{self.machine_id}":
                self.handle_award(data)
            
            elif msg.topic == f"rejects/{self.machine_id}":
                self.handle_rejection(data)
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ERROR] [{self.machine_id}] Error: {e}")
    
    def handle_cfp(self, data):
        """Handle Call for Proposal."""
        job_id = data.get('job_id')
        job_type = data.get('job_type')
        
        print(f"[CFP] [{self.machine_id}] Received CfP for {job_type} (job: {job_id})")
        
        # Check if busy
        if self.busy:
            print(f"[BUSY] [{self.machine_id}] Busy - rejecting CfP")
            self.send_rejection(job_id, "Machine is busy")
            return
        
        # Check if we can do this job
        if job_type not in self.capabilities:
            print(f"[SKIP] [{self.machine_id}] Cannot do {job_type} - rejecting")
            self.send_rejection(job_id, f"Cannot perform {job_type}")
            return
        
        # Submit bid
        self.submit_bid(job_id, job_type)
    
    def submit_bid(self, job_id, job_type):
        """Submit a bid for a job."""
        job_time = self.capabilities[job_type]
        
        # Add some random variation (+/- 10%)
        variation = job_time * random.uniform(-0.1, 0.1)
        bid_time = max(1, job_time + variation)
        
        bid = {
            'type': 'proposal',
            'machine_id': self.machine_id,
            'job_id': job_id,
            'job_type': job_type,
            'time': round(bid_time, 2),
            'capabilities': list(self.capabilities.keys()),
            'timestamp': time.time()
        }
        
        self.client.publish(f"bids/{job_id}", json.dumps(bid))
        self.bids_submitted += 1
        print(f"[BID] [{self.machine_id}] Bid submitted: {bid_time:.2f}s for {job_type}")
    
    def send_rejection(self, job_id, reason):
        """Send rejection for a CfP."""
        rejection = {
            'type': 'reject',
            'machine_id': self.machine_id,
            'job_id': job_id,
            'reason': reason,
            'timestamp': time.time()
        }
        self.client.publish(f"bids/{job_id}", json.dumps(rejection))
    
    def handle_award(self, data):
        """Handle job award - start working."""
        job_id = data.get('job_id')
        job_type = data.get('job_type')
        
        if job_type not in self.capabilities:
            print(f"[WARN] [{self.machine_id}] Awarded unknown job type: {job_type}")
            return
        
        job_time = self.capabilities[job_type]
        
        print(f"[WIN] [{self.machine_id}] WON job {job_id}! Starting {job_type}...")
        self.bids_won += 1
        
        # Start job execution
        self.busy = True
        self.current_job = {'job_id': job_id, 'job_type': job_type}
        self.job_end_time = time.time() + job_time
        
        # Execute job in background
        def execute_job():
            print(f"[WORK] [{self.machine_id}] Working on {job_type} for {job_time}s...")
            time.sleep(job_time)
            self.busy = False
            self.current_job = None
            self.jobs_completed += 1
            print(f"[DONE] [{self.machine_id}] Completed job {job_id}! "
                  f"(Total: {self.jobs_completed})")
        
        threading.Thread(target=execute_job, daemon=True).start()
    
    def handle_rejection(self, data):
        """Handle bid rejection."""
        job_id = data.get('job_id')
        print(f"[LOST] [{self.machine_id}] Bid rejected for job {job_id}")
    
    def run(self):
        try:
            print(f"[MACHINE] [{self.machine_id}] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print(f"\n[STOP] [{self.machine_id}] Interrupted")
        except Exception as e:
            print(f"[ERROR] [{self.machine_id}] Error: {e}")
        finally:
            print(f"[STATS] [{self.machine_id}] Bids: {self.bids_submitted}, "
                  f"Won: {self.bids_won}, Completed: {self.jobs_completed}")
            self.running = False
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Contract Net Machine Agent')
    parser.add_argument('--id', dest='machine_id', required=True, help='Machine ID')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--capabilities', nargs='+', 
                        default=['assembly:5', 'inspection:3'],
                        help='Capabilities in format job:time (e.g., assembly:5 welding:10)')
    args = parser.parse_args()
    
    # Parse capabilities
    capabilities = {}
    for cap in args.capabilities:
        parts = cap.split(':')
        if len(parts) == 2:
            capabilities[parts[0]] = float(parts[1])
    
    if not capabilities:
        capabilities = {'assembly': 5, 'inspection': 3}
    
    machine = MachineAgent(
        machine_id=args.machine_id,
        capabilities=capabilities,
        broker=args.broker,
        port=args.port
    )
    machine.run()


if __name__ == "__main__":
    main()
