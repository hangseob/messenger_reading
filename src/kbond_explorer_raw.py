import win32gui
import win32con

def get_window_info(hwnd):
    title = win32gui.GetWindowText(hwnd)
    cls = win32gui.GetClassName(hwnd)
    return title, cls

def enum_child_windows(parent_hwnd):
    children = []
    def callback(hwnd, param):
        title, cls = get_window_info(hwnd)
        # Try to get text content
        text = ""
        if cls in ["Edit", "Static", "TRichEdit", "TMemo", "TEdit"]:
            length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
            buffer = win32gui.PyMakeBuffer(length + 1)
            win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buffer)
            text = buffer[:length].tobytes().decode('ansi', errors='ignore')
        
        children.append({
            "hwnd": hwnd,
            "title": title,
            "class": cls,
            "text": text
        })
        return True
    
    win32gui.EnumChildWindows(parent_hwnd, callback, None)
    return children

def explore_kbond_raw():
    target_classes = ["TfrmDccChat"]
    all_windows = []
    def enum_top_windows(hwnd, param):
        if win32gui.IsWindowVisible(hwnd):
            title, cls = get_window_info(hwnd)
            if cls in target_classes or any(name in title for name in ["정민후", "조인목", "도진용"]):
                all_windows.append((hwnd, title, cls))
        return True
    
    win32gui.EnumWindows(enum_top_windows, None)
    
    for hwnd, title, cls in all_windows:
        print(f"\nWindow: '{title}' (Class: {cls}, Hwnd: {hwnd})")
        children = enum_child_windows(hwnd)
        for child in children:
            if child['text'] or child['class'] != 'TPanel': # Filter out too many panels
                print(f"  Child: {child['hwnd']}, Class: {child['class']}, Title: '{child['title']}', Text: '{child['text'][:100]}...'")

if __name__ == "__main__":
    explore_kbond_raw()
