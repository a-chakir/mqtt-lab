#!/usr/bin/env python3
"""
Ping-Pong Game Starter - Part I.2
Master process that spawns both ping and pong clients automatically.
"""

import subprocess
import sys
import time
import os
import signal


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ping_pong_script = os.path.join(script_dir, 'ping_pong.py')
    
    print("[GAME] Starting Ping-Pong Game...")
    print("=" * 40)
    
    # Start pong player first (receiver)
    print("[GAME] Spawning PONG player...")
    pong_process = subprocess.Popen(
        [sys.executable, ping_pong_script, '--mode', 'pong', '--rounds', '10'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    time.sleep(0.5)  # Give pong time to connect
    
    # Start ping player (initiator)
    print("[GAME] Spawning PING player...")
    ping_process = subprocess.Popen(
        [sys.executable, ping_pong_script, '--mode', 'ping', '--rounds', '10'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("=" * 40)
    print("[GAME] Game in progress... Press Ctrl+C to stop\n")
    
    try:
        # Read and display output from both processes
        import threading
        
        def read_output(process, name):
            for line in process.stdout:
                print(f"[{name}] {line}", end='')
        
        ping_thread = threading.Thread(target=read_output, args=(ping_process, "PING"))
        pong_thread = threading.Thread(target=read_output, args=(pong_process, "PONG"))
        
        ping_thread.start()
        pong_thread.start()
        
        # Wait for both processes to complete
        ping_process.wait()
        pong_process.wait()
        
        ping_thread.join()
        pong_thread.join()
        
    except KeyboardInterrupt:
        print("\n[STOP] Stopping game...")
        ping_process.terminate()
        pong_process.terminate()
        ping_process.wait()
        pong_process.wait()
    
    print("\n[GAME] Game Over!")


if __name__ == "__main__":
    main()
