import json
import time
import sys
import os
from src.kbond_monitor import KBondMonitor
from src.message_writer import AsyncMessageWriter

def main():
    # Load config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Update filename for KBond
    config['output']['filename_format'] = "kbond_messages_{timestamp}.txt"
    
    # Initialize writer
    writer = AsyncMessageWriter(config)
    writer.start()
    
    def on_message(msg):
        # Format the message for display and saving
        display_text = f"[{msg['window']}] {msg['text']}"
        print(f"\n[NEW] {display_text}")
        
        # Save message
        writer.write_message({
            'timestamp': msg['timestamp'],
            'text': display_text
        })

    # Initialize monitor
    monitor = KBondMonitor(on_message, config)
    
    print("="*50)
    print("KBond Messenger Monitoring System")
    print("Target Windows: TfrmDccChat (Chat Windows)")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop()
        writer.stop()

if __name__ == "__main__":
    main()
