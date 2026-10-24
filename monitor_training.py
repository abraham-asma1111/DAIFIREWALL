#!/usr/bin/env python3
"""
Training Monitor Script
Shows real-time progress of RL agent training

"""

import time
import os
import re
from datetime import datetime, timedelta

TOTAL_TIMESTEPS = 2_800_000
LOG_FILE = "training_all_data.log"

def extract_latest_metrics():
    """Extract latest timesteps from log file"""
    if not os.path.exists(LOG_FILE):
        return None, None, None
    
    try:
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        
        # Find all timestep entries
        timestep_matches = re.findall(r'total_timesteps\s+\|\s+(\d+)', content)
        fps_matches = re.findall(r'fps\s+\|\s+(\d+)', content)
        
        if timestep_matches and fps_matches:
            latest_timesteps = int(timestep_matches[-1])
            latest_fps = int(fps_matches[-1])
            return latest_timesteps, latest_fps, None
        
        return None, None, None
    except Exception as e:
        return None, None, str(e)

def format_time(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"

def main():
    print("="*70)
    print("DYNAMIC AI FIREWALL - TRAINING MONITOR")
    print("="*70)
    print()
    print("Monitoring training progress... Press Ctrl+C to stop")
    print()
    
    last_timesteps = 0
    last_check_time = time.time()
    
    while True:
        try:
            # Extract metrics
            timesteps, fps, error = extract_latest_metrics()
            
            if error:
                print(f"Error reading log: {error}")
                time.sleep(5)
                continue
            
            if timesteps is None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for training to start...")
                time.sleep(5)
                continue
            
            # Calculate progress
            progress_pct = (timesteps / TOTAL_TIMESTEPS) * 100
            remaining = TOTAL_TIMESTEPS - timesteps
            
            if fps and fps > 0:
                eta_seconds = remaining / fps
                eta_str = format_time(eta_seconds)
                completion_time = datetime.now() + timedelta(seconds=eta_seconds)
                completion_str = completion_time.strftime('%H:%M:%S')
            else:
                eta_str = "calculating..."
                completion_str = "calculating..."
            
            # Calculate actual speed (timesteps per second since last check)
            current_time = time.time()
            time_elapsed = current_time - last_check_time
            if last_timesteps > 0 and time_elapsed > 0:
                actual_fps = (timesteps - last_timesteps) / time_elapsed
            else:
                actual_fps = fps if fps else 0
            
            # Progress bar
            bar_width = 40
            filled = int(bar_width * timesteps / TOTAL_TIMESTEPS)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            # Clear line and print status
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{bar} {progress_pct:.1f}% | "
                  f"{timesteps:,}/{TOTAL_TIMESTEPS:,} | "
                  f"{int(actual_fps)} fps | "
                  f"ETA: {eta_str} ({completion_str})", 
                  end='', flush=True)
            
            # Check if complete
            if os.path.exists("models/firewall_all_data.zip"):
                print("\n")
                print("="*70)
                print("✅ TRAINING COMPLETE!")
                print("="*70)
                print(f"\nModel saved: models/firewall_all_data.zip")
                print(f"\nNext steps:")
                print(f"  1. Run pipeline: ./run_pipeline.sh")
                print(f"  2. Or run manually: python src/rl_agent/evaluate.py")
                print()
                break
            
            # Update for next iteration
            last_timesteps = timesteps
            last_check_time = current_time
            
            # Wait before next check
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            print(f"\nCurrent progress: {timesteps:,}/{TOTAL_TIMESTEPS:,} ({progress_pct:.1f}%)")
            print(f"To resume monitoring, run: python monitor_training.py")
            print()
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
