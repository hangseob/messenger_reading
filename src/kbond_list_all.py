import win32gui
import sys

# Ensure Korean output works
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def enum_windows_callback(hwnd, results):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        if title:
            results.append((hwnd, title, class_name))

def main():
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    print(f"Total visible windows: {len(windows)}")
    for hwnd, title, cls in windows:
        if cls == "TfrmDccChat" or any(name in title for name in ["정민후", "조인목", "도진용"]):
            print(f"HWND: {hwnd}, Class: {cls}, Title: {title}")
            
            # List children
            def child_callback(h, p):
                t = win32gui.GetWindowText(h)
                c = win32gui.GetClassName(h)
                print(f"  Child HWND: {h}, Class: {c}, Title: {t}")
                return True
            win32gui.EnumChildWindows(hwnd, child_callback, None)

if __name__ == "__main__":
    main()
