import time
import sys
from .hook import start_hook, stop_hook

def run():
    print("="*50)
    print("KBond Custom Right-Click Tool (Win32 TrackPopupMenu)")
    print("Features: '문장복사', '모두복사'")
    print("Requirement: Run as Administrator")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    try:
        start_hook()
    except KeyboardInterrupt:
        print("\nStopping tool...")
    finally:
        stop_hook()

if __name__ == "__main__":
    run()
