# KBond Custom Right-Click Tool

## 테스트 기록
- 2026.01.30 17:47: Queue + 메인 스레드 Tkinter 방식 테스트 완료, 정상 동작

---

## 해결한 기술적 이슈

### 1. Tkinter 스레딩 문제
**증상**: `Tcl_AsyncDelete: async handler deleted by the wrong thread`
**원인**: Tkinter는 메인 스레드에서만 실행 가능한데, 별도 스레드에서 호출
**해결**: Queue를 사용하여 메인 스레드에서 Tkinter 메뉴 표시

### 2. Win32 TrackPopupMenu 실패
**증상**: 메뉴가 즉시 닫힘 (cmd=0 반환)
**원인**: TrackPopupMenu는 메시지 루프가 있는 스레드에서만 정상 동작
**해결**: Win32 API 대신 Tkinter 사용, 메인 스레드에서 실행

### 3. KBond 메신저 Crash
**증상**: 커스텀 메뉴 사용 후 KBond가 응답 없음/다운
**원인**: SendMessage 호출 시 deadlock, 또는 KBond 메뉴 강제 종료 시도
**해결**: 
- `SendMessageTimeout` 사용 (100ms 타임아웃)
- `IsHungAppWindow`로 응답 여부 확인
- 데이터 pre-fetch (우클릭 DOWN 시점에 미리 읽음)
- 메뉴 표시 시 KBond와 추가 통신 없음

### 4. Native 메뉴 겹침
**증상**: KBond 기본 우클릭 메뉴와 커스텀 메뉴가 동시에 표시
**해결**: `close_popup_menus()`로 #32768 클래스 팝업 메뉴에 WM_CLOSE 전송

### 5. Stale Data 문제
**증상**: 이전 클릭의 데이터가 복사됨
**해결**: `clear_pending_data()`로 매 클릭마다 글로벌 데이터 초기화

---

## 최종 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN THREAD                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PeekMessage Loop (Non-blocking)                    │   │
│  │    ↓                                                │   │
│  │  Queue.get_nowait() → 메뉴 요청 확인               │   │
│  │    ↓                                                │   │
│  │  show_tkinter_menu() → Tkinter 메뉴 표시 ✓         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↑ Queue
┌─────────────────────────────────────────────────────────────┐
│                  WORKER THREADS                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │ WM_RBUTTONDOWN      │  │ WM_RBUTTONUP                │  │
│  │   ↓                 │  │   ↓                         │  │
│  │ prepare_and_fetch() │  │ queue_menu_request()        │  │
│  │   ↓                 │  │   ↓                         │  │
│  │ prefetch_data()     │  │ pending_data → Queue        │  │
│  │   - is_kbond 체크   │  └─────────────────────────────┘  │
│  │   - get_all_text()  │                                   │
│  │   - 문장 추출       │                                   │
│  └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

## 핵심 설계 원칙

1. **메인 스레드에서 UI 처리**: Tkinter는 반드시 메인 스레드에서 실행
2. **Hook 콜백 최소화**: mouse_handler는 스레드 생성만 하고 즉시 반환
3. **Pre-fetch 전략**: 우클릭 DOWN 시점에 데이터 수집 (팝업 뜨기 전)
4. **타임아웃 보호**: 모든 SendMessage 호출에 타임아웃 적용
5. **외부 창 참조 없음**: 더미 창, 다른 창 핸들 사용 안 함

## 파일 구조

```
src/kbond_right_click/
├── __init__.py
├── main.py          # 진입점
├── hook.py          # 마우스 훅 + Queue 처리
├── menu.py          # Tkinter 메뉴 (메인 스레드용)
├── utils.py         # KBond 창 감지, 텍스트 추출
└── readme.md        # 이 문서

src/kbond_right_click_win32/  # 백업 (Win32 TrackPopupMenu 버전)
```
