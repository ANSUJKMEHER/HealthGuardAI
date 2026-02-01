import time
import sys
from main import HealthGuardSystem

def print_banner():
    banner = """
    ██   ██ ███████  █████  ██      ████████ ██   ██      ██████  ██    ██  █████  ██████  ██████      █████  ██ 
    ██   ██ ██      ██   ██ ██         ██    ██   ██     ██       ██    ██ ██   ██ ██   ██ ██   ██    ██   ██ ██ 
    ███████ █████   ███████ ██         ██    ███████     ██   ███ ██    ██ ███████ ██████  ██   ██    ███████ ██ 
    ██   ██ ██      ██   ██ ██         ██    ██   ██     ██    ██ ██    ██ ██   ██ ██   ██ ██   ██    ██   ██ ██ 
    ██   ██ ███████ ██   ██ ███████    ██    ██   ██      ██████   ██████  ██   ██ ██   ██ ██████     ██   ██ ██ 
                                                                                                                   
    >>> AUTONOMOUS INFRASTRUCTURE SENTINEL <<<
    """
    print(banner)

def run_demo():
    print_banner()
    
    # Initialize System
    hg = HealthGuardSystem()
    hg.start()
    
    try:
        # Phase 1: Normal Operation
        print("\n--- [PHASE 1] Checking Normal Operation (10s) ---")
        for i in range(10):
            metrics = hg.monitored_system.get_metrics()
            print(f"[Tick {i+1}] CPU: {metrics['cpu_percent']}%, Memory: {metrics['memory_mb']}MB")
            time.sleep(1)
            
        # Phase 2: Inject Critical Failure
        print("\n\n--- [PHASE 2] 💉 INJECTING FAILURE: MEMORY LEAK ---")
        hg.monitored_system.inject_failure("MEMORY_LEAK")
        
        # Phase 3: Observe Agent Reaction
        print("\n--- [PHASE 3] WATCHING AGENTS REACT ---")
        print("(Agents should detect anomaly, diagnose it, fix it, and report)\n")
        
        # Wait for the agent loop to handle it (Monitor takes ~2s, Fix ~3s, Verify ~3s)
        # We'll just loop and print status until we see recovery or timeout
        recovered = False
        for i in range(20):
            metrics = hg.monitored_system.get_metrics()
            if metrics['active_failure'] is None and metrics['memory_mb'] < 100:
                 recovered = True
                 # But we want to let the agent print its report first
            
            # Print current state
            note = "⚠️ CRITICAL" if metrics['memory_mb'] > 300 else "✅ STABLE"
            print(f"[Time {i+1}s] State: {note} | CPU: {metrics['cpu_percent']}% | Mem: {metrics['memory_mb']}MB")
            
            if recovered and i > 10: # Give time for report to flush
                print("\n--- [PHASE 4] DEMO COMPLETE: SUCCESS ---")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Demo] Aborted by user.")
    finally:
        hg.stop()
        print("[Demo] System Shutdown.")

if __name__ == "__main__":
    run_demo()
