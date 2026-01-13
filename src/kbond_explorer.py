import win32gui
import win32process
from pywinauto import Application

def enum_windows_callback(hwnd, results):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        if title:
            results.append((hwnd, title, class_name))

def explore_kbond():
    print("Enumerating all visible windows...")
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    kbond_windows = []
    target_names = ["정민후", "조인목", "도진용", "KBond"]
    
    for hwnd, title, cls in windows:
        if any(name in title for name in target_names):
            kbond_windows.append((hwnd, title, cls))
            
    if not kbond_windows:
        print("No KBond related windows found.")
        # Print all visible windows to help debug
        # for hwnd, title, cls in windows[:10]:
        #     print(f"Hwnd: {hwnd}, Title: {title}, Class: {cls}")
        return

    for hwnd, title, cls in kbond_windows:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        print(f"\n--- Found Window: '{title}' ---")
        print(f"  Hwnd: {hwnd}, Class: {cls}, PID: {pid}")
        
        try:
            # Try connecting via handle
            print("  Attempting to get control identifiers (win32)...")
            app = Application(backend="win32").connect(handle=hwnd)
            win = app.window(handle=hwnd)
            win.print_control_identifiers()
            
            print("\n  Attempting to get control identifiers (uia)...")
            app_uia = Application(backend="uia").connect(handle=hwnd)
            win_uia = app_uia.window(handle=hwnd)
            win_uia.print_control_identifiers()
            
        except Exception as e:
            print(f"  Error exploring window: {e}")

if __name__ == "__main__":
    explore_kbond()
