import time
import threading
import hashlib
from datetime import datetime
from typing import Optional, Callable, List, Dict
import psutil
from pywinauto import Application
import win32gui
import win32process
import win32con
import pyperclip

class MultiKakaoMonitor:
    def __init__(self, callback: Callable[[Dict], None], config: dict):
        self.callback = callback
        self.config = config
        self.is_running = False
        self._history = set()
        self.app = None
        self.process_name = "KakaoTalk.exe"
        self._window_snapshots = {}  # 각 창의 마지막 텍스트 상태 저장

    def connect(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.process_name:
                    self.app = Application(backend="win32").connect(process=proc.info['pid'])
                    return True
        except:
            pass
        return False

    def find_all_chat_windows(self) -> List[Dict]:
        """현재 열려 있는 모든 카카오톡 대화창 정보를 가져옵니다."""
        pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == self.process_name:
                pid = proc.info['pid']
                break
        
        if not pid: return []
        
        chat_windows = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
                if win_pid == pid:
                    title = win32gui.GetWindowText(hwnd)
                    if title and title not in ["카카오톡", "MSCTFIME UI", "Default IM"]:
                        chat_windows.append({'hwnd': hwnd, 'title': title})
            return True
        
        win32gui.EnumWindows(callback, None)
        return chat_windows

    def quick_capture_text(self, hwnd) -> str:
        """창을 빠르게 활성화하고 텍스트를 복사합니다 (0.3초 이내)"""
        try:
            # 이전 클립보드 내용 백업
            old_clip = pyperclip.paste()
            pyperclip.copy("")
            
            # 창 활성화 (매우 짧게)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.05)
            
            # 복사 명령 전송
            win = self.app.window(handle=hwnd)
            win.type_keys("^a^c")
            time.sleep(0.15)
            
            # 복사된 텍스트 가져오기
            result = pyperclip.paste()
            
            # 클립보드 복원
            pyperclip.copy(old_clip)
            
            return result
        except:
            return ""

    def extract_new_lines(self, current_text: str, window_title: str):
        """현재 텍스트와 이전 스냅샷을 비교하여 새로 추가된 라인만 추출합니다."""
        if not current_text:
            return []
        
        # 해시 생성 (전체 텍스트로 변경 감지)
        text_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
        
        # 이전 스냅샷과 비교
        prev_snapshot = self._window_snapshots.get(window_title, {})
        prev_hash = prev_snapshot.get('hash', '')
        prev_lines = prev_snapshot.get('lines', set())
        
        # 텍스트가 변하지 않았으면 건너뛰기
        if text_hash == prev_hash:
            return []
        
        # 현재 텍스트를 라인별로 분리
        current_lines = [line.strip() for line in current_text.split('\r\n') if line.strip()]
        current_lines_set = set(current_lines)
        
        # 새로운 라인들만 추출 (이전에 없던 것)
        new_lines = []
        for line in current_lines:
            # 입력창/시스템 메시지 필터링
            if any(word in line for word in ["메시지 입력", "전송", "RichEdit Control"]):
                continue
            
            # 중복 체크
            line_id = f"{window_title}_{line}"
            line_hash = hashlib.md5(line_id.encode('utf-8')).hexdigest()
            
            if line_hash not in self._history and line not in prev_lines:
                new_lines.append({
                    'text': f"[{window_title}] {line}",
                    'timestamp': datetime.now(),
                    'hash': line_hash
                })
                self._history.add(line_hash)
        
        # 스냅샷 업데이트
        self._window_snapshots[window_title] = {
            'hash': text_hash,
            'lines': current_lines_set
        }
        
        return new_lines

    def monitoring_loop(self):
        print("[INFO] Fast clipboard-based multi-window monitoring started")
        print("[INFO] Window switching is minimized for better user experience")
        
        # 초기화: 모든 창의 현재 상태를 스냅샷으로 저장 (첫 실행시 모든 메시지가 쏟아지지 않도록)
        print("[INFO] Initializing window snapshots...")
        windows = self.find_all_chat_windows()
        for win_info in windows:
            text = self.quick_capture_text(win_info['hwnd'])
            if text:
                self._window_snapshots[win_info['title']] = {
                    'hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
                    'lines': set([line.strip() for line in text.split('\r\n') if line.strip()])
                }
                # 초기 히스토리에도 추가
                for line in text.split('\r\n'):
                    line = line.strip()
                    if line:
                        line_id = f"{win_info['title']}_{line}"
                        self._history.add(hashlib.md5(line_id.encode('utf-8')).hexdigest())
        
        print(f"[INFO] Initialized {len(windows)} chat windows")
        print("[OK] Monitoring for NEW messages only...\n")
        
        while self.is_running:
            if not self.app:
                if not self.connect():
                    time.sleep(2)
                    continue

            windows = self.find_all_chat_windows()
            
            for win_info in windows:
                if not self.is_running: break
                
                try:
                    # 텍스트 빠르게 캡처
                    text = self.quick_capture_text(win_info['hwnd'])
                    
                    # 새로운 라인만 추출
                    new_messages = self.extract_new_lines(text, win_info['title'])
                    
                    # 콜백 호출
                    for msg in new_messages:
                        self.callback(msg)
                        
                except Exception as e:
                    continue
                
                # 창 전환 간격 (매우 짧게)
                time.sleep(0.1)
            
            # 한 사이클이 끝나면 설정된 간격만큼 대기
            time.sleep(self.config['kakao']['monitoring_interval'])

    def start(self):
        if not self.connect():
            print("[ERROR] Failed to connect to KakaoTalk")
            return False
        self.is_running = True
        self.thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.is_running = False
