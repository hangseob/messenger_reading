"""
카카오톡 실시간 메시지 추출 프로그램
메시지를 0.5초 이내에 TXT 파일로 저장
"""
import json
import time
import signal
import sys
from pathlib import Path
from src.kakao_monitor import KakaoMonitor
from src.message_writer import AsyncMessageWriter, SyncMessageWriter
from src.performance_monitor import PerformanceMonitor


class KakaoMessageReader:
    def __init__(self, config_path: str = "config.json"):
        """
        Args:
            config_path: 설정 파일 경로
        """
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 성능 모니터
        self.perf_monitor = PerformanceMonitor(
            max_response_time=self.config['performance']['max_response_time']
        )
        
        # 파일 쓰기 (비동기/동기 선택)
        if self.config['performance']['use_async']:
            self.writer = AsyncMessageWriter(self.config)
        else:
            self.writer = SyncMessageWriter(self.config)
        
        # 카카오톡 모니터
        self.monitor = KakaoMonitor(
            callback=self.on_message_received,
            config=self.config
        )
        
        # 종료 시그널 핸들러
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def on_message_received(self, message: dict):
        """
        새 메시지 수신 시 호출되는 콜백
        
        Args:
            message: 메시지 딕셔너리
        """
        start_time = time.time()
        
        # 메시지를 파일에 쓰기
        self.writer.write_message(message)
        
        # 응답 시간 측정
        response_time = time.time() - start_time
        self.perf_monitor.record_response_time(response_time)
        
        # 콘솔 출력
        print(f"[MSG] [{message['timestamp'].strftime('%H:%M:%S')}] {message['text'][:50]}... "
              f"({response_time*1000:.1f}ms)")
    
    def signal_handler(self, signum, frame):
        """종료 시그널 처리"""
        print("\n\n[INFO] Stop signal received...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """프로그램 시작"""
        print("="*60)
        print("RUN: KakaoTalk Real-time Message Extractor")
        print("="*60)
        print(f"Target response time: {self.config['performance']['max_response_time']*1000}ms")
        print(f"Monitoring interval: {self.config['kakao']['monitoring_interval']*1000}ms")
        print("="*60 + "\n")
        
        # 파일 쓰기 시작
        self.writer.start()
        
        # 모니터링 시작
        if not self.monitor.start():
            print("\n[ERROR] Could not start monitoring.")
            print("\nCheck list:")
            print("  1. Is KakaoTalk running?")
            print("  2. Try running as Administrator")
            print("  3. Is KakaoTalk window open?")
            return False
        
        print("\n[OK] Monitoring started!")
        print("INFO: Press Ctrl+C to stop.\n")
        print("-"*60)
        
        return True
    
    def stop(self):
        """프로그램 종료"""
        # 모니터링 중지
        self.monitor.stop()
        
        # 파일 쓰기 중지
        self.writer.stop()
        
        # 통계 출력
        self.perf_monitor.print_statistics()
        
        print("[OK] Program terminated.")
    
    def run(self):
        """메인 실행 루프"""
        if not self.start():
            return
        
        try:
            # 메인 스레드는 대기 상태 유지
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n[INFO] User interrupted...")
        finally:
            self.stop()


def main():
    """프로그램 진입점"""
    print("[INFO] Starting application...")
    
    # 설정 파일 확인
    config_path = Path("config.json")
    if not config_path.exists():
        print("[ERROR] config.json not found.")
        return
    
    try:
        app = KakaoMessageReader(config_path=str(config_path))
        app.run()
    except Exception as e:
        import traceback
        print(f"\n[FATAL] Crash detected: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
