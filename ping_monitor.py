import subprocess
import time
import threading
from datetime import datetime
import os
import sys

TARGETS_FILE = "targets.txt"
LOG_FILE = "downtime_log.txt"
PING_INTERVAL = 3  # Seconds between pings

def log_event(target, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {status}: {target}"
    print(message)
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def ping_target(target):
    # Hide the console window of the ping subprocess (Windows specific)
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # -n 1 (send 1 packet), -w 1000 (wait 1000ms for reply)
    command = ['ping', '-n', '1', '-w', '1000', target]
    
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        output = result.stdout.decode('cp437', errors='ignore').lower()
        
        # On Windows, unreachable hosts can still return exit code 0, 
        # so we must check for "ttl=" to confirm a successful reply.
        if result.returncode != 0 or "ttl=" not in output:
            return False
        return True
    except Exception:
        return False

def monitor_target(target):
    was_down = False
    print(f"Started monitoring: {target}")
    
    while True:
        is_up = ping_target(target)
        
        if not is_up and not was_down:
            log_event(target, "DOWN")
            was_down = True
        elif is_up and was_down:
            log_event(target, "RESTORED")
            was_down = False
            
        time.sleep(PING_INTERVAL)

def main():
    print("=== Portable Ping Monitor ===")
    
    # Create target file if it doesn't exist
    if not os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, "w") as f:
            f.write("# Add IPs or Hostnames below (one per line)\n8.8.8.8\n1.1.1.1\n")
        print(f"Created '{TARGETS_FILE}'. Please add your IPs to this file and restart the app.")
        input("Press Enter to exit...")
        sys.exit()

    # Read targets
    with open(TARGETS_FILE, "r") as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not targets:
        print(f"No targets found. Please add IPs to {TARGETS_FILE}.")
        input("Press Enter to exit...")
        sys.exit()

    print(f"Loaded {len(targets)} targets. Press Ctrl+C to stop.\n")
    
    # Start a background thread for each target
    threads = []
    for target in targets:
        t = threading.Thread(target=monitor_target, args=(target,), daemon=True)
        t.start()
        threads.append(t)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()