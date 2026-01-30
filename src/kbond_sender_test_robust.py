from pywinauto import Application, Desktop
import time
import sys

def send_message_robust(target_title, text):
    try:
        # Use pywinauto to find the window by title snippet
        desktop = Desktop(backend="win32")
        # Try to find window containing target_title
        target_win = None
        for win in desktop.windows():
            if target_title in win.window_text() and win.class_name() == "TfrmDccChat":
                target_win = win
                break
        
        if not target_win:
            print(f"Error: Could not find window containing '{target_title}'")
            return False
            
        print(f"Found window: {target_win.window_text()}")
        target_win.set_focus()
        time.sleep(0.5)
        
        # Find the input field - it's the one that is NOT readonly
        import win32gui
        import win32con
        input_field = None
        for ctrl in target_win.descendants():
            if "RichEdit" in ctrl.class_name():
                hwnd = ctrl.handle
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if not (style & win32con.ES_READONLY):
                    input_field = ctrl
                    break
        
        if not input_field:
            print("Error: Could not find editable RichEdit control.")
            return False
            
        print(f"Found input field class: {input_field.class_name()}")
        
        # Click it to be sure
        input_field.click_input()
        time.sleep(0.2)
        
        # Use type_keys which is most likely to trigger internal Delphi events
        input_field.type_keys(text + "{ENTER}", with_spaces=True, set_foreground=True)
        
        print(f"Sent message via type_keys: '{text}'")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Ensure stdout handles Korean for logging
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    target = "정민후"
    message = "자동메세지 테스트입니다"
    send_message_robust(target, message)
