"""
성능 모니터링 유틸리티
응답 시간 추적 및 성능 통계
"""
import time
from collections import deque
from typing import Optional


class PerformanceMonitor:
    def __init__(self, max_response_time: float = 0.5):
        """
        Args:
            max_response_time: 최대 허용 응답 시간 (초)
        """
        self.max_response_time = max_response_time
        self.response_times = deque(maxlen=1000)  # 최근 1000개 기록
        self.violations = 0  # 응답 시간 초과 횟수
        self.total_messages = 0
        
    def record_response_time(self, response_time: float):
        """응답 시간 기록"""
        self.response_times.append(response_time)
        self.total_messages += 1
        
        if response_time > self.max_response_time:
            self.violations += 1
            print(f"⚠️  응답 시간 초과: {response_time*1000:.1f}ms (목표: {self.max_response_time*1000:.1f}ms)")
    
    def get_average_response_time(self) -> Optional[float]:
        """평균 응답 시간 계산"""
        if not self.response_times:
            return None
        return sum(self.response_times) / len(self.response_times)
    
    def get_statistics(self) -> dict:
        """성능 통계 반환"""
        if not self.response_times:
            return {}
        
        times = list(self.response_times)
        times.sort()
        
        return {
            'total_messages': self.total_messages,
            'average_ms': self.get_average_response_time() * 1000,
            'min_ms': min(times) * 1000,
            'max_ms': max(times) * 1000,
            'p50_ms': times[len(times)//2] * 1000,
            'p95_ms': times[int(len(times)*0.95)] * 1000,
            'p99_ms': times[int(len(times)*0.99)] * 1000,
            'violations': self.violations,
            'violation_rate': (self.violations / self.total_messages * 100) if self.total_messages > 0 else 0
        }
    
    def print_statistics(self):
        """통계 출력"""
        stats = self.get_statistics()
        if not stats:
            print("📊 통계 데이터 없음")
            return
        
        print("\n" + "="*60)
        print("📊 성능 통계")
        print("="*60)
        print(f"총 메시지:        {stats['total_messages']:,}개")
        print(f"평균 응답 시간:   {stats['average_ms']:.2f}ms")
        print(f"최소 응답 시간:   {stats['min_ms']:.2f}ms")
        print(f"최대 응답 시간:   {stats['max_ms']:.2f}ms")
        print(f"P50 (중앙값):     {stats['p50_ms']:.2f}ms")
        print(f"P95:              {stats['p95_ms']:.2f}ms")
        print(f"P99:              {stats['p99_ms']:.2f}ms")
        print(f"목표 초과:        {stats['violations']:,}회 ({stats['violation_rate']:.1f}%)")
        print("="*60 + "\n")
