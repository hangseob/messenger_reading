import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes
import threading
import time
from .utils import get_window_at_pos, is_kbond_chat_history, is_text_selected, get_sentence_at_pos, get_all_text
from .menu import show_custom_menu

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

# 우클릭 DOWN 시점에 저장할 데이터
pending_data = {
    'hwnd': None,
    'x': 0,
    'y': 0,
    'is_kbond': False,
    'is_selected': False,
    'sentence': '',
    'all_text': ''
}

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_longlong

def show_menu_with_data():
    """저장된 데이터로 메뉴를 표시합니다."""
    time.sleep(0.15)  # 약간의 딜레이
    
    if pending_data['is_kbond'] and not pending_data['is_selected']:
        print(f"[DEBUG] Showing menu with pre-fetched data...")
        show_custom_menu(
            pending_data['hwnd'],
            pending_data['x'],
            pending_data['y'],
            pending_data['sentence'],
            pending_data['all_text']
        )
    else:
        print(f"[DEBUG] Conditions not met. is_kbond={pending_data['is_kbond']}, is_selected={pending_data['is_selected']}")

def mouse_handler(nCode, wParam, lParam):
    global is_shutting_down, pending_data
    if is_shutting_down:
        return user32.CallNextHookEx(None, nCode, wParam, lParam)
        
    try:
        if nCode >= 0:
            data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            x, y = data.pt.x, data.pt.y
            
            if wParam == win32con.WM_RBUTTONDOWN:
                # DOWN 시점에 모든 데이터를 미리 읽어놓음 (팝업이 뜨기 전)
                hwnd = get_window_at_pos(x, y)
                cls_name = win32gui.GetClassName(hwnd) if hwnd else "None"
                print(f"\n[DEBUG] ========== RIGHT-CLICK DOWN at ({x}, {y}) ==========")
                print(f"[DEBUG] HWND: {hwnd}, Class: {cls_name}")
                
                is_kbond = is_kbond_chat_history(hwnd)
                print(f"[DEBUG] is_kbond_chat_history: {is_kbond}")
                
                if is_kbond:
                    is_selected = is_text_selected(hwnd)
                    print(f"[DEBUG] is_text_selected: {is_selected}")
                    
                    if not is_selected:
                        # 텍스트를 미리 읽어놓음
                        print(f"[DEBUG] Pre-fetching text...")
                        sentence = get_sentence_at_pos(hwnd, x, y)
                        all_text = get_all_text(hwnd)
                        print(f"[DEBUG] Sentence: '{sentence[:50] if sentence else 'EMPTY'}...'")
                        print(f"[DEBUG] All text length: {len(all_text) if all_text else 0}")
                        
                        pending_data = {
                            'hwnd': hwnd,
                            'x': x,
                            'y': y,
                            'is_kbond': True,
                            'is_selected': False,
                            'sentence': sentence,
                            'all_text': all_text
                        }
                    else:
                        pending_data['is_kbond'] = False
                else:
                    pending_data['is_kbond'] = False
                    
            elif wParam == win32con.WM_RBUTTONUP:
                print(f"[DEBUG] ========== RIGHT-CLICK UP ==========")
                # UP 시점에는 저장된 데이터로 메뉴를 띄움
                if pending_data['is_kbond'] and not pending_data['is_selected']:
                    threading.Thread(target=show_menu_with_data, daemon=True).start()
                    
    except Exception as e:
        print(f"[DEBUG] Hook Error: {e}")
    
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
    print("[DEBUG] Now capturing data on RIGHT-CLICK DOWN (before popup).")
    
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
        print("\n[INFO] Mouse hook uninstalled.")
