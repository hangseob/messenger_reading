import win32gui
import win32con
import ctypes
from ctypes import wintypes
import time

# SendMessageTimeout 설정
user32 = ctypes.windll.user32
SMTO_ABORTIFHUNG = 0x0002
SMTO_BLOCK = 0x0001

def ts():
    """밀리초 타임스탬프 반환"""
    return time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"

def send_message_timeout(hwnd, msg, wparam, lparam, timeout_ms=100):
    """SendMessageTimeout wrapper - 타임아웃을 100ms로 단축"""
    if not win32gui.IsWindow(hwnd):
        return 0
    result = ctypes.c_ulong()
    success = user32.SendMessageTimeoutW(
        hwnd, msg, wparam, lparam,
        SMTO_ABORTIFHUNG, timeout_ms,
        ctypes.byref(result)
    )
    if success:
        return result.value
    return 0

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

def get_window_at_pos(x, y):
    """Returns the window handle at the given screen coordinates."""
    try:
        return win32gui.WindowFromPoint((x, y))
    except:
        return None

def get_room_name(hwnd):
    """TfrmDccChat 창의 제목(채팅방 이름)을 가져옵니다."""
    try:
        parent = win32gui.GetParent(hwnd)
        while parent:
            p_cls = win32gui.GetClassName(parent)
            if p_cls == "TfrmDccChat":
                return win32gui.GetWindowText(parent)
            parent = win32gui.GetParent(parent)
        return "Unknown"
    except:
        return "Unknown"

def get_window_info(hwnd):
    """KBond 창의 상태 정보를 수집합니다. Crash 감지용."""
    info = {
        'hwnd': hwnd,
        'valid': False,
        'title': '',
        'class': '',
        'parent_title': '',
        'visible': False,
        'enabled': False,
        'responding': False,
        'style': 0
    }
    
    try:
        if not hwnd:
            return info
            
        # 창이 유효한지 확인
        if not win32gui.IsWindow(hwnd):
            print(f"[{ts()}] WARN: Window {hwnd} is no longer valid!")
            return info
        
        info['valid'] = True
        
        # 클래스명
        try:
            info['class'] = win32gui.GetClassName(hwnd)
        except:
            pass
        
        # 창 제목 (타임아웃으로 안전하게)
        try:
            title_len = send_message_timeout(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0, 50)
            if title_len > 0 and title_len < 256:
                buffer = ctypes.create_unicode_buffer(title_len + 1)
                result = ctypes.c_ulong()
                success = user32.SendMessageTimeoutW(
                    hwnd, win32con.WM_GETTEXT, title_len + 1, buffer,
                    SMTO_ABORTIFHUNG, 100, ctypes.byref(result)
                )
                if success:
                    info['title'] = buffer.value
        except:
            pass
        
        # 부모 창 제목 (채팅방 이름) - TfrmDccChat 창의 제목 사용
        try:
            info['parent_title'] = get_room_name(hwnd)
        except:
            pass
        
        # Visible / Enabled 상태
        try:
            info['visible'] = bool(win32gui.IsWindowVisible(hwnd))
            info['enabled'] = bool(win32gui.IsWindowEnabled(hwnd))
        except:
            pass
        
        # 응답 여부 확인 (핵심 crash 지표!)
        try:
            # IsHungAppWindow는 창이 응답하지 않으면 True 반환
            is_hung = user32.IsHungAppWindow(hwnd)
            info['responding'] = not bool(is_hung)
            if is_hung:
                print(f"[{ts()}] ⚠️ CRITICAL: Window {hwnd} is NOT RESPONDING!")
        except:
            info['responding'] = True  # API 실패 시 일단 True로
        
        # 창 스타일
        try:
            info['style'] = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        except:
            pass
            
    except Exception as e:
        print(f"[{ts()}] get_window_info error: {e}")
    
    return info

def log_window_status(hwnd, context=""):
    """창 상태를 상세히 로깅합니다."""
    info = get_window_info(hwnd)
    
    status = "✓ OK" if info['responding'] else "✗ HUNG"
    room_name = info['parent_title'] if info['parent_title'] else "Unknown"
    
    print(f"[{ts()}] === WINDOW STATUS ({context}) ===")
    print(f"[{ts()}]   Room: \"{room_name}\"")
    print(f"[{ts()}]   HWND: {info['hwnd']}, Class: {info['class']}")
    print(f"[{ts()}]   Valid: {info['valid']}, Visible: {info['visible']}, Enabled: {info['enabled']}")
    print(f"[{ts()}]   Responding: {status}")
    
    return info

def is_kbond_chat_history(hwnd):
    """Checks if the hwnd is a ReadOnly RichEdit inside a KBond chat window."""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
            
        cls = win32gui.GetClassName(hwnd)
        if "RichEdit" not in cls:
            return False
        
        # Check if it's read-only (ES_READONLY = 0x800)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        is_readonly = bool(style & 0x800)
        if not is_readonly:
            return False
        
        # 모든 부모 창을 순회하며 TfrmDccChat 찾기 (원래 로직 복구!)
        parent = win32gui.GetParent(hwnd)
        while parent:
            p_cls = win32gui.GetClassName(parent)
            if p_cls == "TfrmDccChat":
                return True
            parent = win32gui.GetParent(parent)
        
        return False
    except:
        return False

def is_text_selected(hwnd):
    """Checks if any text is currently selected."""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        result = send_message_timeout(hwnd, win32con.EM_GETSEL, 0, 0, 50)
        start = result & 0xFFFF
        end = (result >> 16) & 0xFFFF
        return start != end
    except:
        return False

def extract_sentence_from_text(hwnd, all_text, x, y):
    """
    전체 텍스트에서 문장을 추출합니다.
    
    ⚠️ 중요: EM_CHARFROMPOS, EM_LINEFROMCHAR 호출 제거!
    KBond와의 추가 통신 없이 순수 텍스트 처리만 수행합니다.
    좌표 기반 추출 대신 마지막 메시지(최신)를 반환합니다.
    """
    if not all_text:
        return ""
    try:
        lines = [line.strip() for line in all_text.splitlines() if line.strip()]
        if lines:
            # 마지막 메시지(가장 최근) 반환
            return lines[-1]
        return ""
    except:
        return ""

def get_all_text(hwnd):
    """Extracts all text from the RichEdit control using SendMessageTimeout."""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return ""
        
        # 먼저 창이 응답하는지 확인
        is_hung = user32.IsHungAppWindow(hwnd)
        if is_hung:
            print(f"[{ts()}] ⚠️ get_all_text: Window is HUNG, skipping!")
            return ""
            
        length = send_message_timeout(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0, 100)
        if 0 < length < 1000000:  # 1MB 이상의 텍스트는 무시 (안전)
            buffer = ctypes.create_unicode_buffer(length + 1)
            # WM_GETTEXT with timeout
            result = ctypes.c_ulong()
            success = user32.SendMessageTimeoutW(
                hwnd, win32con.WM_GETTEXT, length + 1, buffer,
                SMTO_ABORTIFHUNG, 200,
                ctypes.byref(result)
            )
            if success:
                return buffer.value
        return ""
    except Exception as e:
        print(f"[{ts()}] get_all_text error: {e}")
        return ""
