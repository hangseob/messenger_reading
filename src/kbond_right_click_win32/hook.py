"""
Win32 TrackPopupMenu 버전 - 별도 스레드에서 메뉴 표시 시도
⚠️ 알려진 문제: TrackPopupMenu가 별도 스레드에서 호출되면 즉시 0 반환
"""
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes
import threading
import time
from .utils import (
    get_window_at_pos, is_kbond_chat_history, is_text_selected, 
    get_all_text, extract_sentence_from_text, log_window_status, get_window_info,
    get_room_name
)
from .menu import show_custom_menu

def ts():
    """밀리초 타임스탬프 반환"""
    return time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"

# Win32 Structures
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]

user32 = ctypes.windll.user32
hook_id = None
_hook_ptr = None
is_shutting_down = False

# 마지막으로 접근한 KBond 창 정보 (crash 추적용)
last_kbond_hwnd = None
last_kbond_room = ""

# 우클릭 DOWN 시점에 저장할 데이터 (글로벌 딕셔너리)
pending_data = {
    'hwnd': None,
    'room_name': '',
    'x': 0,
    'y': 0,
    'is_kbond': False,
    'sentence': '',
    'all_text': ''
}

# 안전장치: 작업 타임아웃 (초)
OPERATION_TIMEOUT = 3.0

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_longlong

def clear_pending_data():
    """글로벌 변수를 완전히 초기화하여 Stale Data 문제를 방지합니다."""
    global pending_data
    pending_data.update({
        'hwnd': None,
        'room_name': '',
        'x': 0,
        'y': 0,
        'is_kbond': False,
        'sentence': '',
        'all_text': ''
    })
    print(f"[{ts()}] Global data RESET")

def check_last_window_health():
    """마지막으로 접근한 KBond 창의 상태를 확인합니다."""
    global last_kbond_hwnd, last_kbond_room
    
    if last_kbond_hwnd:
        try:
            is_hung = user32.IsHungAppWindow(last_kbond_hwnd)
            is_valid = win32gui.IsWindow(last_kbond_hwnd)
            
            if is_hung:
                print(f"[{ts()}] ⚠️⚠️⚠️ CRASH DETECTED! Room \"{last_kbond_room}\" (hwnd={last_kbond_hwnd}) is NOT RESPONDING!")
            elif not is_valid:
                print(f"[{ts()}] ⚠️ Window closed: Room \"{last_kbond_room}\" (hwnd={last_kbond_hwnd})")
                last_kbond_hwnd = None
                last_kbond_room = ""
        except:
            pass

def run_with_timeout(func, args=(), timeout=OPERATION_TIMEOUT):
    """함수를 타임아웃과 함께 실행. 타임아웃 시 None 반환."""
    result = [None]
    exception = [None]
    
    def wrapper():
        try:
            result[0] = func(*args)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        print(f"[{ts()}] WARN: Operation timed out after {timeout}s: {func.__name__}")
        return None
    
    if exception[0]:
        print(f"[{ts()}] WARN: Operation failed: {func.__name__} - {exception[0]}")
        return None
    
    return result[0]

def show_menu_with_data():
    """저장된 데이터로 메뉴를 표시합니다."""
    global pending_data, last_kbond_hwnd, last_kbond_room
    time.sleep(0.15)  # 약간의 딜레이
    
    print(f"[{ts()}] show_menu_with_data: is_kbond={pending_data['is_kbond']}, room=\"{pending_data['room_name']}\"")
    
    # 메뉴 표시 전 마지막 창 상태 확인
    check_last_window_health()
    
    if pending_data['is_kbond']:
        # 1. 데이터를 로컬 변수로 복사
        x, y = pending_data['x'], pending_data['y']
        sentence = pending_data['sentence']
        all_text = pending_data['all_text']
        room = pending_data['room_name']
        
        print(f"[{ts()}] Data for menu: room=\"{room}\", sentence_len={len(sentence)}, all_text_len={len(all_text)}")
        
        # 2. 메뉴 표시 전 글로벌 데이터 비우기 (중요!)
        clear_pending_data()
        
        # 3. 메뉴 호출 (hwnd 없이 - 메뉴는 KBond와 직접 통신하지 않음)
        print(f"[{ts()}] Calling show_custom_menu for room \"{room}\"...")
        show_custom_menu(x, y, sentence, all_text)
        print(f"[{ts()}] show_custom_menu returned.")
        
        # 4. 메뉴 종료 후 마지막 창 상태 다시 확인
        check_last_window_health()
        
    else:
        print(f"[{ts()}] Not a KBond target, clearing data...")
        clear_pending_data()

def prefetch_data(hwnd, x, y):
    """텍스트 데이터를 미리 가져옵니다."""
    global pending_data, last_kbond_hwnd, last_kbond_room
    
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            print(f"[{ts()}] prefetch_data: Invalid hwnd={hwnd}")
            pending_data['is_kbond'] = False
            return
        
        # 창 상태 상세 로깅
        info = log_window_status(hwnd, "PREFETCH START")
        
        # 창이 응답하지 않으면 즉시 중단
        if not info['responding']:
            print(f"[{ts()}] ⚠️ Window not responding, aborting prefetch!")
            pending_data['is_kbond'] = False
            return

        is_kbond = is_kbond_chat_history(hwnd)
        is_selected = is_text_selected(hwnd) if is_kbond else False
        
        room_name = info['parent_title'] if info['parent_title'] else "Unknown"
        
        print(f"[{ts()}] prefetch_data: is_kbond={is_kbond}, is_selected={is_selected}")
        
        if is_kbond and not is_selected:
            # 마지막 접근 창 정보 저장 (crash 추적용)
            last_kbond_hwnd = hwnd
            last_kbond_room = room_name
            
            print(f"[{ts()}] 📌 Accessing KBond room: \"{room_name}\"")
            print(f"[{ts()}] Pre-fetching text (WM_GETTEXT only, no EM_* calls)...")
            
            # 전체 텍스트를 '딱 한 번'만 읽어옴
            all_text = get_all_text(hwnd)
            
            # 텍스트 가져온 후 창 상태 다시 확인
            info_after = get_window_info(hwnd)
            if not info_after['responding']:
                print(f"[{ts()}] ⚠️ Window became unresponsive after get_all_text!")
            
            if all_text:
                # 순수 Python 처리로 문장 추출 (KBond 추가 통신 없음)
                sentence = extract_sentence_from_text(hwnd, all_text, x, y)
                
                print(f"[{ts()}] Text fetched: sentence_len={len(sentence) if sentence else 0}, all_text_len={len(all_text)}")
                
                # 글로벌 딕셔너리 업데이트
                pending_data.update({
                    'hwnd': hwnd,
                    'room_name': room_name,
                    'x': x,
                    'y': y,
                    'is_kbond': True,
                    'sentence': sentence or '',
                    'all_text': all_text
                })
                print(f"[{ts()}] pending_data UPDATED: room=\"{room_name}\"")
            else:
                print(f"[{ts()}] Failed to get text from KBond")
                pending_data['is_kbond'] = False
        else:
            pending_data['is_kbond'] = False
            
    except Exception as e:
        print(f"[{ts()}] prefetch_data error: {e}")
        pending_data['is_kbond'] = False

def prepare_and_fetch(x, y):
    """별도 스레드에서 API 호출 수행 - 후킹 콜백 부하 최소화"""
    global last_kbond_hwnd
    
    # 새 클릭 전 마지막 창 상태 확인
    check_last_window_health()
    
    clear_pending_data()
    print(f"\n[{ts()}] ========== RIGHT-CLICK DOWN at ({x}, {y}) ==========")
    
    hwnd = get_window_at_pos(x, y)
    if hwnd:
        try:
            cls_name = win32gui.GetClassName(hwnd)
            print(f"[{ts()}] Target: hwnd={hwnd}, class={cls_name}")
        except:
            pass
    
    run_with_timeout(prefetch_data, (hwnd, x, y), OPERATION_TIMEOUT)

def mouse_handler(nCode, wParam, lParam):
    global is_shutting_down
    # 후킹 콜백은 최대한 짧고 빠르게 리턴해야 커서 소실이 안 생깁니다.
    if nCode < 0 or is_shutting_down:
        return user32.CallNextHookEx(hook_id, nCode, wParam, lParam)
        
    try:
        if wParam == win32con.WM_RBUTTONDOWN:
            data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            # 모든 API 호출을 스레드로 분리
            threading.Thread(target=lambda: prepare_and_fetch(data.pt.x, data.pt.y), daemon=True).start()
        elif wParam == win32con.WM_RBUTTONUP:
            print(f"[{ts()}] ========== RIGHT-CLICK UP ==========")
            threading.Thread(target=show_menu_with_data, daemon=True).start()
    except:
        pass
    
    return user32.CallNextHookEx(hook_id, nCode, wParam, lParam)

def start_hook():
    global hook_id, _hook_ptr, is_shutting_down
    is_shutting_down = False
    _hook_ptr = HOOKPROC(mouse_handler)
    
    hook_id = user32.SetWindowsHookExW(14, _hook_ptr, win32api.GetModuleHandle(None), 0)
    if not hook_id:
        print("Error: Could not install mouse hook.")
        return

    print("Mouse hook installed. Monitoring KBond right-clicks...")
    print(f"[INFO] Safety: All operations timeout after {OPERATION_TIMEOUT}s")
    print(f"[INFO] KBond interaction: WM_GETTEXT only (no EM_* calls)")
    print(f"[INFO] Menu does NOT hold KBond hwnd reference")
    print(f"[INFO] Crash detection: IsHungAppWindow monitoring enabled")
    
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except (KeyboardInterrupt, SystemExit):
        is_shutting_down = True
    finally:
        stop_hook()

def stop_hook():
    global hook_id, is_shutting_down
    is_shutting_down = True
    if hook_id:
        user32.UnhookWindowsHookEx(hook_id)
        hook_id = None
        print(f"\n[{ts()}] Mouse hook uninstalled cleanly.")
