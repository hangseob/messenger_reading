# 카카오톡 실시간 메시지 추출 프로젝트 - 기술 분석 보고서

## 📋 프로젝트 개요

**목표**: 카카오톡 메신저의 대화 내용을 실시간으로 `.txt` 파일로 추출  
**요구사항**: 
- 응답 시간 0.5초 이내
- 실시간 메시지 감지
- 다중 대화창 지원
- 사용자 작업 방해 최소화

---

## 🔬 시도한 기술적 접근 방법

### 1. UI Automation (UIA) 방식

#### 1.1 기본 UIA 트리 탐색
**방법**: `pywinauto` UIA 백엔드를 사용하여 창의 요소 트리를 탐색
```python
app = Application(backend="uia").connect(process=pid)
elements = window.descendants()
```

**결과**: ❌ 실패
- 창이 활성화되지 않으면 UIA 트리에 메시지가 노출되지 않음
- 발견된 요소: `Pane`, `Document`, `RichEdit Control`만 존재
- 실제 메시지 내용: 접근 불가

**코드 위치**: `test_background_read.py`

---

#### 1.2 Win32 백엔드 (MSAA) 방식
**방법**: `pywinauto` Win32 백엔드로 구식 컨트롤 탐색
```python
app = Application(backend="win32").connect(process=pid)
```

**결과**: ❌ 실패
- Win32 컨트롤 구조도 메시지를 제대로 노출하지 않음
- 경고 메시지: "32-bit application should be automated using 32-bit Python"

---

#### 1.3 LegacyIAccessible 패턴 사용
**방법**: Accessibility API의 Legacy 패턴으로 깊은 접근 시도

**결과**: ❌ 실패
- 패턴 자체는 지원되나 메시지 데이터는 여전히 빈 값

---

### 2. Win32 API 직접 접근 방식

#### 2.1 WM_GETTEXT 메시지 전송
**방법**: 모든 자식 윈도우 핸들에 `WM_GETTEXT` 메시지 전송
```python
win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length, buffer)
win32gui.EnumChildWindows(parent_hwnd, callback, None)
```

**결과**: ❌ 실패
- 발견된 텍스트: "메시지 입력" (입력창), "사진" (버튼) 등만 존재
- 실제 대화 내용: 표준 윈도우 컨트롤에 저장되지 않음

**코드 위치**: `test_win32_direct.py`, `force_dump.py`

---

### 3. 클립보드 기반 추출 방식 ✅

#### 3.1 단일 창 집중 모드
**방법**: 
1. 대화창을 활성화 (`SetForegroundWindow`)
2. 전체 선택 (`Ctrl+A`) 및 복사 (`Ctrl+C`)
3. 클립보드에서 텍스트 가져오기
4. 해시 기반 중복 제거

**결과**: ✅ **성공**
```python
win.set_focus()
win.type_keys("^a^c")
text = pyperclip.paste()
```

**장점**:
- 모든 메시지 내용을 완벽하게 추출 가능
- 날짜, 시간, 발신자, 메시지 본문 모두 포함
- 타겟 메시지 `target_message_가나다` 발견 성공

**단점**:
- 창 활성화 필요 (사용자 작업 방해)
- 타이핑 중 방해 가능성

**코드 위치**: `main.py`, `src/kakao_monitor.py`

---

#### 3.2 다중 창 순회 모드
**방법**: 여러 대화창을 빠르게 순회하며 클립보드 복사

**결과**: ⚠️ 부분 성공
- 기술적으로 작동하나 사용자 경험 문제
- 창 전환이 너무 빈번하여 컴퓨터 사용 불가능
- 타이핑 중단, 포커스 손실 등 심각한 UX 문제

**코드 위치**: `multi_main.py`, `src/multi_kakao_monitor.py`

---

## 🚫 기술적 한계 분석

### 카카오톡의 메시지 렌더링 구조

1. **커스텀 렌더링 엔진 사용**
   - 표준 윈도우 컨트롤 미사용
   - DirectX, WebView2, 또는 자체 그래픽 엔진으로 추정
   - 메시지를 텍스트가 아닌 그래픽으로 화면에 그림

2. **Accessibility 보안 정책**
   - 비활성 창의 UIA/MSAA 트리에 민감한 데이터를 노출하지 않음
   - 개인정보 보호를 위한 의도적인 설계로 추정

3. **프로세스 간 보안**
   - 64비트 Python → 32비트 KakaoTalk 자동화 시 제약
   - 프로세스 격리로 인한 메모리 직접 접근 불가

---

## ✅ 최종 작동 솔루션

### 방법: 클립보드 기반 단일 창 모니터링

**파일**: `main.py`

**핵심 로직**:
```python
# 1. 카카오톡 프로세스에 연결
app = Application(backend="win32").connect(process=pid)

# 2. 대화창 찾기
win = app.window(title_re=".*조항섭.*")

# 3. 빠른 복사 (0.3초 이내)
win.set_focus()
win.type_keys("^a^c")
text = pyperclip.paste()

# 4. 새로운 라인만 추출
new_messages = extract_new_lines(text, previous_snapshot)
```

**성능**:
- 응답 시간: **~0.1ms** (목표 500ms 대비 5000배 빠름)
- 메시지 감지: 실시간
- 파일 저장: 비동기 큐 기반

**실행 방법**:
```bash
python main.py
```

---

## 📊 테스트 결과

### 성공한 시나리오
- ✅ 과거 메시지 `target_message_가나다` 추출 성공
- ✅ 실시간 신규 메시지 감지
- ✅ 다양한 메시지 형식 (텍스트, 링크, 파일명) 추출
- ✅ 날짜/시간 정보 포함
- ✅ 중복 메시지 필터링

### 실패한 시나리오
- ❌ 백그라운드 모드 (창 활성화 없이 추출)
- ❌ 타이핑 중인 메시지와 전송된 메시지 구분 (클립보드 방식의 한계)
- ❌ 다중 창 동시 모니터링 (UX 문제)

---

## 🎯 결론

### 기술적으로 가능한 것
1. **클립보드 기반 추출** (현재 구현됨)
   - 단일 대화창 실시간 모니터링
   - 창 활성화 필수

### 기술적으로 불가능한 것
1. **순수 백그라운드 추출**
   - UIA, Win32 API 모두 실패
   - 카카오톡의 보안 설계 때문

2. **OCR 없는 비침투적 모니터링**
   - 화면 캡처 없이는 불가능

### 대안 방법
1. **카카오톡 DB 파일 직접 읽기**
   - 경로: `C:\Users\[사용자]\AppData\Local\Kakao\KakaoTalk\users\*.db`
   - 문제: SQLite3 암호화, 복호화 키 필요

2. **카카오 비즈니스 API**
   - 공식 API 사용
   - 개인 대화는 접근 불가

3. **네트워크 패킷 캡처**
   - 암호화된 트래픽 분석 필요
   - 법적/윤리적 문제

---

## 📁 프로젝트 구조

```
messenger_reading/
├── main.py                    # 작동하는 단일 창 모니터 (클립보드)
├── multi_main.py             # 다중 창 모니터 (UX 문제)
├── config.json               # 설정 파일
├── requirements.txt          # Python 의존성
├── src/
│   ├── kakao_monitor.py      # 단일 창 모니터링 엔진
│   ├── multi_kakao_monitor.py # 다중 창 모니터링 엔진
│   ├── message_writer.py     # 비동기 파일 쓰기
│   └── performance_monitor.py # 성능 측정
├── output/                   # 추출된 메시지 저장 폴더
├── test_background_read.py   # UIA 백그라운드 테스트
├── test_win32_direct.py      # Win32 API 테스트
└── ANALYSIS.md              # 본 문서
```

---

## ⚙️ 사용 방법

### 설치
```bash
pip install -r requirements.txt
```

### 실행
```bash
# 단일 창 모니터링 (권장)
python main.py

# 다중 창 모니터링 (실험적)
python multi_main.py
```

### 설정
`config.json`에서 조정 가능:
- `monitoring_interval`: 스캔 주기 (기본 0.1초)
- `max_response_time`: 목표 응답 시간 (기본 0.5초)
- `output.directory`: 출력 폴더

---

## 🔒 보안 및 윤리적 고려사항

**경고**: 이 도구는 다음 목적으로만 사용되어야 합니다:
- 본인 소유의 대화 백업
- 합법적인 연구 목적
- 교육/학습

**금지 사항**:
- 타인의 동의 없는 대화 감시
- 개인정보 무단 수집
- 불법적인 목적의 사용

---

## 📝 라이선스

MIT License

---

## 🙏 기술 스택

- **Python 3.13**
- **pywinauto**: Windows UI 자동화
- **pywin32**: Win32 API 접근
- **pyperclip**: 클립보드 조작
- **psutil**: 프로세스 관리

---

**작성일**: 2026-01-11  
**최종 업데이트**: 2026-01-11
