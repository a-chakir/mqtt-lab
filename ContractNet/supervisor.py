#!/usr/bin/env python3
"""
Supervisor Agent - Part III.1
Implements the Contract Net protocol supervisor:
- Generates jobs
- Sends Call for Proposals (CfP)
- Collects bids
- Selects winner and assigns job
"""

import paho.mqtt.client as mqtt
import time
import argparse
import json
import uuid
import threading
from collections import defaultdict


class SupervisorAgent:
    def __init__(self, broker='localhost', port=1883, bid_deadline=5):
        self.broker = broker
        self.port = port
        self.bid_deadline = bid_deadline  # seconds to wait for bids
        self.running = True
        
        # Job types that can be generated
        self.job_types = ['assembly', 'welding', 'painting', 'inspection', 'packaging']
        
        # Current CfP state
        self.current_job = None
        self.collected_bids = {}  # machine_id -> bid info
        self.bid_lock = threading.Lock()
        self.bid_event = threading.Event()
        
        # Statistics
        self.jobs_completed = 0
        self.jobs_failed = 0
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   client_id="supervisor")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[SUPERVISOR] Connected to broker!")
            # Subscribe to bids
            client.subscribe("bids/+")  # bids/<job_id>
            print("[SUPERVISOR] Ready to dispatch jobs")
        else:
            print(f"[ERROR] [SUPERVISOR] Connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming bids."""
        try:
            data = json.loads(msg.payload.decode())
            job_id = msg.topic.split('/')[-1]
            
            # Only accept bids for current job
            if self.current_job and job_id == self.current_job['job_id']:
                machine_id = data.get('machine_id')
                
                if data.get('type') == 'proposal':
                    with self.bid_lock:
                        self.collected_bids[machine_id] = {
                            'time': data.get('time', float('inf')),
                            'machine_id': machine_id,
                            'capabilities': data.get('capabilities', [])
                        }
                    print(f"[BID] Received bid from {machine_id}: {data.get('time')}s")
                
                elif data.get('type') == 'reject':
                    print(f"[REJECT] Rejection from {machine_id}")
                    
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ERROR] [SUPERVISOR] Error parsing bid: {e}")
    
    def generate_job(self):
        """Generate a random job."""
        import random
        job_type = random.choice(self.job_types)
        return {
            'job_id': str(uuid.uuid4())[:8],
            'type': job_type,
            'priority': random.randint(1, 5),
            'timestamp': time.time()
        }
    
    def send_cfp(self, job):
        """Send Call for Proposal to all machines."""
        cfp = {
            'type': 'cfp',
            'job_id': job['job_id'],
            'job_type': job['type'],
            'priority': job['priority'],
            'deadline': self.bid_deadline,
            'timestamp': time.time()
        }
        
        self.client.publish("cfp/jobs", json.dumps(cfp))
        print(f"\n[CFP] CfP sent for job {job['job_id']} ({job['type']})")
    
    def evaluate_bids(self):
        """Evaluate collected bids and select winner."""
        with self.bid_lock:
            bids = dict(self.collected_bids)
        
        if not bids:
            print("[FAIL] No bids received - job cannot be assigned")
            return None
        
        # Select the machine with the lowest time
        winner = min(bids.values(), key=lambda x: x['time'])
        print(f"[WINNER] Selected {winner['machine_id']} (time: {winner['time']}s)")
        return winner
    
    def send_award(self, job, winner):
        """Send job award to winner and rejections to others."""
        # Award message to winner
        award = {
            'type': 'award',
            'job_id': job['job_id'],
            'job_type': job['type'],
            'timestamp': time.time()
        }
        
        award_topic = f"awards/{winner['machine_id']}"
        self.client.publish(award_topic, json.dumps(award))
        print(f"[AWARD] Job {job['job_id']} awarded to {winner['machine_id']}")
        
        # Send rejections to other bidders
        with self.bid_lock:
            for machine_id in self.collected_bids:
                if machine_id != winner['machine_id']:
                    reject = {
                        'type': 'reject_bid',
                        'job_id': job['job_id'],
                        'reason': 'Another machine was selected',
                        'timestamp': time.time()
                    }
                    self.client.publish(f"rejects/{machine_id}", json.dumps(reject))
                    print(f"[REJECT] Bid rejected: {machine_id}")
    
    def dispatch_job(self, job):
        """Complete Contract Net round for a job."""
        self.current_job = job
        
        with self.bid_lock:
            self.collected_bids.clear()
        
        # Phase 1: Send CfP
        self.send_cfp(job)
        
        # Phase 2: Wait for bids (deadline)
        print(f"[WAIT] Waiting {self.bid_deadline}s for bids...")
        time.sleep(self.bid_deadline)
        
        # Phase 3: Evaluate bids
        winner = self.evaluate_bids()
        
        if winner:
            # Phase 4: Award job
            self.send_award(job, winner)
            self.jobs_completed += 1
        else:
            self.jobs_failed += 1
        
        self.current_job = None
        return winner is not None
    
    def run(self, num_jobs=10, job_interval=3):
        """Run the supervisor, generating and dispatching jobs."""
        try:
            print(f"[SUPERVISOR] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            time.sleep(2)  # Wait for machines to be ready
            
            print("\n" + "=" * 60)
            print("     CONTRACT NET PROTOCOL - JOB SCHEDULING")
            print("=" * 60)
            
            for i in range(num_jobs):
                if not self.running:
                    break
                
                print(f"\n{'='*60}")
                print(f"     JOB {i+1}/{num_jobs}")
                print(f"{'='*60}")
                
                job = self.generate_job()
                success = self.dispatch_job(job)
                
                print(f"\n[STATS] Completed: {self.jobs_completed}, Failed: {self.jobs_failed}")
                
                if i < num_jobs - 1:
                    time.sleep(job_interval)
            
            print("\n" + "=" * 60)
            print("     FINAL STATISTICS")
            print("=" * 60)
            print(f"     Jobs Completed: {self.jobs_completed}")
            print(f"     Jobs Failed:    {self.jobs_failed}")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n[STOP] [SUPERVISOR] Interrupted")
        except Exception as e:
            print(f"[ERROR] [SUPERVISOR] Error: {e}")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            print("[SUPERVISOR] Disconnected")


def main():
    parser = argparse.ArgumentParser(description='Contract Net Supervisor')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--jobs', type=int, default=10, help='Number of jobs to dispatch')
    parser.add_argument('--deadline', type=int, default=5, help='Bid deadline in seconds')
    parser.add_argument('--interval', type=int, default=3, help='Interval between jobs')
    args = parser.parse_args()
    
    supervisor = SupervisorAgent(
        broker=args.broker,
        port=args.port,
        bid_deadline=args.deadline
    )
    supervisor.run(num_jobs=args.jobs, job_interval=args.interval)


if __name__ == "__main__":
    main()
