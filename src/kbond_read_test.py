import win32gui
import win32con
import ctypes
import sys

# Ensure Korean output works
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def get_text_safe(hwnd):
    length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    if length > 0:
        buffer = ctypes.create_unicode_buffer(length + 1)
        win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buffer)
        return buffer.value
    return ""

def main():
    target_names = ["도진용", "조인목", "정민후"]
    def enum_top_windows(hwnd, param):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if any(name in title for name in target_names):
                print(f"\n--- Window: {title} (HWND: {hwnd}) ---")
                
                def enum_children(h, p):
                    cls = win32gui.GetClassName(h)
                    if "RichEdit" in cls:
                        text = get_text_safe(h)
                        if text:
                            print(f"  [{cls}] {h}: {text[:200]}...")
                    return True
                
                win32gui.EnumChildWindows(hwnd, enum_children, None)
        return True

    win32gui.EnumWindows(enum_top_windows, None)

if __name__ == "__main__":
    main()
