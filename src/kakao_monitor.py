import time
import threading
import hashlib
from datetime import datetime
from typing import Optional, Callable, List, Dict
import psutil
import win32gui
import win32con
import win32process
import pyperclip
from pywinauto import Application

class KakaoMonitor:
    def __init__(self, callback: Callable[[Dict], None], config: dict):
        self.callback = callback
        self.config = config
        self.is_running = False
        self._history = set()
        self._last_clipboard = ""
        self.target_string = "target_message_가나다"
        self.app = None

    def find_kakao_process(self) -> Optional[int]:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'KakaoTalk.exe':
                return proc.info['pid']
        return None

    def connect(self):
        pid = self.find_kakao_process()
        if pid:
            self.app = Application(backend="win32").connect(process=pid)
            return True
        return False

    def find_chat_window(self, target_title="조항섭"):
        if not self.app: return None
        try:
            return self.app.window(title_re=f".*{target_title}.*")
        except: return None

    def capture_via_clipboard(self, win):
        """
        창을 활성화하고 클립보드로 복사합니다.
        """
        try:
            pyperclip.copy("")
            # 창을 활성화해야 복사가 확실함
            win.set_focus()
            time.sleep(0.1)
            
            # Ctrl+A, Ctrl+C
            win.type_keys("^a^c")
            time.sleep(0.3)
            
            return pyperclip.paste()
        except Exception as e:
            return ""

    def process_raw_text(self, text: str, window_title: str) -> List[Dict]:
        if not text: return []
        
        lines = text.split('\r\n')
        messages = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 타겟 메시지 체크
            if self.target_string in line:
                print(f"\nSUCCESS - Found Target: {line}")
            
            msg_hash = hashlib.md5(f"{window_title}_{line}".encode('utf-8')).hexdigest()
            if msg_hash not in self._history:
                messages.append({
                    'text': f"[{window_title}] {line}",
                    'timestamp': datetime.now(),
                    'hash': msg_hash
                })
                self._history.add(msg_hash)
        
        return messages

    def monitoring_loop(self):
        print(f"INFO: Clipboard Monitoring Engine Started (Target: {self.target_string})")
        
        while self.is_running:
            try:
                win = self.find_chat_window("조항섭")
                if win and win.exists():
                    raw_text = self.capture_via_clipboard(win)
                    
                    if raw_text:
                        if raw_text != self._last_clipboard:
                            print(f"INFO: New data captured from clipboard ({len(raw_text)} chars)")
                            self._last_clipboard = raw_text
                        
                        new_msgs = self.process_raw_text(raw_text, "조항섭")
                        for m in new_msgs:
                            self.callback(m)
                
                time.sleep(self.config['kakao']['monitoring_interval'])
            except Exception as e:
                time.sleep(1)

    def start(self):
        if not self.connect():
            print("ERROR: Failed to connect to KakaoTalk.")
            return False
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        return True

    def stop(self):
        self.is_running = False
