import win32gui
import win32con
import ctypes
import time
import threading
from datetime import datetime
import hashlib
import sys

# Ensure Korean output works
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class KBondMonitor:
    def __init__(self, callback, config):
        self.callback = callback
        self.config = config
        self.is_running = False
        self._history = {} # window_title -> set of message hashes
        self._last_text_len = {} # window_title -> last seen text length
        self.target_class = "TfrmDccChat"
        self.thread = None

    def get_text_safe(self, hwnd):
        try:
            length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buffer)
                return buffer.value
        except Exception:
            pass
        return ""

    def find_chat_windows(self):
        windows = []
        def enum_cb(hwnd, param):
            if win32gui.IsWindowVisible(hwnd):
                cls = win32gui.GetClassName(hwnd)
                if cls == self.target_class:
                    title = win32gui.GetWindowText(hwnd)
                    windows.append((hwnd, title))
            return True
        win32gui.EnumWindows(enum_cb, None)
        return windows

    def find_history_controls(self, parent_hwnd):
        controls = []
        def enum_cb(hwnd, param):
            cls = win32gui.GetClassName(hwnd)
            if "RichEdit" in cls:
                controls.append(hwnd)
            return True
        win32gui.EnumChildWindows(parent_hwnd, enum_cb, None)
        return controls

    def process_window(self, hwnd, title):
        controls = self.find_history_controls(hwnd)
        if not controls:
            return

        # Usually TJvRichEdit is the main one. Let's find the one with the most text.
        best_text = ""
        for ctrl in controls:
            text = self.get_text_safe(ctrl)
            if len(text) > len(best_text):
                best_text = text

        if not best_text:
            return

        # Check if we've seen this window before
        if title not in self._history:
            self._history[title] = set()
            # On first encounter, we might want to skip existing history 
            # or process all of it. Let's process all for now.
            print(f"INFO: Monitoring new window: {title}")

        lines = best_text.split('\r\n')
        if len(lines) == 1:
            lines = best_text.split('\n')
            
        new_messages = []
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Use hash of the line to identify uniqueness within this window
            msg_hash = hashlib.md5(line.encode('utf-8')).hexdigest()
            if msg_hash not in self._history[title]:
                self._history[title].add(msg_hash)
                new_messages.append({
                    'window': title,
                    'text': line,
                    'timestamp': datetime.now()
                })
        
        for msg in new_messages:
            self.callback(msg)

    def monitoring_loop(self):
        interval = self.config.get('kbond', {}).get('monitoring_interval', 1.0)
        while self.is_running:
            try:
                windows = self.find_chat_windows()
                for hwnd, title in windows:
                    self.process_window(hwnd, title)
                time.sleep(interval)
            except Exception as e:
                # print(f"Error in monitoring loop: {e}")
                time.sleep(2)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.thread.start()
        print("KBond Monitor Started.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("KBond Monitor Stopped.")

if __name__ == "__main__":
    # Test run
    def test_callback(msg):
        print(f"[{msg['timestamp'].strftime('%H:%M:%S')}] {msg['window']}: {msg['text']}")

    config = {'kbond': {'monitoring_interval': 1.0}}
    monitor = KBondMonitor(test_callback, config)
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
