"""
비동기 메시지 파일 출력 시스템
빠른 응답을 위해 큐 기반 비동기 쓰기 사용
"""
import os
import time
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict


class AsyncMessageWriter:
    def __init__(self, config: dict):
        """
        Args:
            config: 출력 설정
        """
        self.config = config
        self.output_dir = Path(config['output']['directory'])
        self.encoding = config['output']['encoding']
        self.append_mode = config['output']['append_mode']
        
        # 비동기 큐
        self.message_queue = queue.Queue(maxsize=config['performance']['buffer_size'])
        self.is_running = False
        self.writer_thread = None
        
        # 출력 파일 경로
        self.output_file = None
        self._prepare_output_file()
        
    def _prepare_output_file(self):
        """출력 파일 준비"""
        # 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config['output']['filename_format'].format(timestamp=timestamp)
        self.output_file = self.output_dir / filename
        
        print(f"[INFO] Output file: {self.output_file}")
    
    def format_message(self, message: Dict) -> str:
        """메시지를 텍스트 포맷으로 변환"""
        timestamp = message['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        text = message['text']
        
        return f"[{timestamp}] {text}\n"
    
    def write_message(self, message: Dict):
        """
        메시지를 큐에 추가 (빠른 응답을 위해 즉시 반환)
        
        Args:
            message: 메시지 딕셔너리
        """
        try:
            # 큐가 가득 찬 경우 즉시 파일에 쓰기
            if self.message_queue.full():
                self._write_to_file(message)
            else:
                self.message_queue.put_nowait(message)
        except queue.Full:
            # 큐가 가득 찬 경우 직접 쓰기
            self._write_to_file(message)
    
    def _write_to_file(self, message: Dict):
        """실제 파일 쓰기 작업"""
        try:
            formatted_text = self.format_message(message)
            mode = 'a' if self.append_mode else 'w'
            
            with open(self.output_file, mode, encoding=self.encoding) as f:
                f.write(formatted_text)
                f.flush()  # 즉시 디스크에 쓰기
                
        except Exception as e:
            print(f"[ERROR] File write error: {e}")
    
    def writer_loop(self):
        """비동기 쓰기 루프"""
        while self.is_running:
            try:
                # 큐에서 메시지 가져오기 (최대 0.1초 대기)
                message = self.message_queue.get(timeout=0.1)
                self._write_to_file(message)
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Writer loop error: {e}")
    
    def start(self):
        """비동기 쓰기 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.writer_thread = threading.Thread(target=self.writer_loop, daemon=True)
        self.writer_thread.start()
        print("[INFO] Async writer started")
    
    def stop(self):
        """비동기 쓰기 중지 (큐의 모든 메시지 처리 후)"""
        print("[INFO] Saving remaining messages...")
        
        # 큐의 모든 메시지 처리 대기
        self.message_queue.join()
        
        self.is_running = False
        if self.writer_thread:
            self.writer_thread.join(timeout=2)
        
        print(f"[INFO] All messages saved: {self.output_file}")


class SyncMessageWriter:
    """동기식 파일 쓰기 (설정에서 비동기 비활성화 시 사용)"""
    
    def __init__(self, config: dict):
        self.config = config
        self.output_dir = Path(config['output']['directory'])
        self.encoding = config['output']['encoding']
        self.append_mode = config['output']['append_mode']
        self.output_file = None
        self._prepare_output_file()
        
    def _prepare_output_file(self):
        """출력 파일 준비"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config['output']['filename_format'].format(timestamp=timestamp)
        self.output_file = self.output_dir / filename
        print(f"[INFO] Output file: {self.output_file}")
    
    def format_message(self, message: Dict) -> str:
        """메시지를 텍스트 포맷으로 변환"""
        timestamp = message['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        text = message['text']
        return f"[{timestamp}] {text}\n"
    
    def write_message(self, message: Dict):
        """메시지 즉시 파일에 쓰기"""
        try:
            formatted_text = self.format_message(message)
            mode = 'a' if self.append_mode else 'w'
            
            with open(self.output_file, mode, encoding=self.encoding) as f:
                f.write(formatted_text)
                f.flush()
        except Exception as e:
            print(f"[ERROR] File write error: {e}")
    
    def start(self):
        """동기 쓰기는 시작 작업 없음"""
        print("[INFO] Sync writer mode")
    
    def stop(self):
        """동기 쓰기는 중지 작업 없음"""
        print(f"[INFO] Saved: {self.output_file}")
