import json
import time
import signal
import sys
from pathlib import Path
from src.multi_kakao_monitor import MultiKakaoMonitor
from src.message_writer import AsyncMessageWriter

class MultiWindowApp:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.writer = AsyncMessageWriter(self.config)
        self.monitor = MultiKakaoMonitor(
            callback=self.on_new_message,
            config=self.config
        )
        
        signal.signal(signal.SIGINT, self.handle_exit)

    def on_new_message(self, message: dict):
        """새로운 메시지가 감지되었을 때만 호출됩니다."""
        # 파일에 쓰기
        self.writer.write_message(message)
        
        # 콘솔 출력
        print(f"[NEW] [{message['timestamp'].strftime('%H:%M:%S')}] {message['text']}")

    def handle_exit(self, sig, frame):
        print("\n[INFO] Stopping...")
        self.monitor.stop()
        self.writer.stop()
        sys.exit(0)

    def run(self):
        print("="*60)
        print("RUN: Multi-Window KakaoTalk Monitor")
        print("Monitoring all open chat windows for NEW messages only.")
        print("="*60)
        
        self.writer.start()
        if self.monitor.start():
            print("[OK] Monitoring is active. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        else:
            print("[ERROR] Failed to start monitor.")

if __name__ == "__main__":
    config_file = Path("config.json")
    if config_file.exists():
        app = MultiWindowApp(str(config_file))
        app.run()
    else:
        print("config.json not found.")
