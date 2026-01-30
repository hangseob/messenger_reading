import win32gui
import win32con
import time
from pywinauto.keyboard import send_keys

def find_kbond_window(target_title):
    target_hwnd = None
    def enum_cb(hwnd, param):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if cls == "TfrmDccChat" and target_title in title:
                target_hwnd = hwnd
                return False
        return True
    try:
        win32gui.EnumWindows(enum_cb, None)
    except:
        pass
    return target_hwnd

def send_message_v3(target_title, text):
    hwnd = find_kbond_window(target_title)
    if not hwnd:
        print(f"Error: Could not find window '{target_title}'")
        return False

    print(f"Found window: {win32gui.GetWindowText(hwnd)} (HWND: {hwnd})")
    
    try:
        # Try to bring to foreground
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Once focused, we just send keys. 
        # In KBond, the input field is usually focused by default or when clicked.
        # We'll assume it's focused or the user has it open.
        # send_keys from pywinauto is quite reliable for sending to active window
        send_keys(text + "{ENTER}")
        
        print(f"Sent keys to window: '{text}'")
        return True
    except Exception as e:
        print(f"Failed to send keys: {e}")
        # If SetForegroundWindow fails, it's definitely a privilege issue.
        print("Tip: Please run the terminal/editor as Administrator.")
        return False

if __name__ == "__main__":
    target = "정민후"
    message = "자동메세지 테스트입니다"
    send_message_v3(target, message)
