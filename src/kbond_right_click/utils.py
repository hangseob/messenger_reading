import win32gui
import win32con
import ctypes
from ctypes import wintypes

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

def get_window_at_pos(x, y):
    """Returns the window handle at the given screen coordinates."""
    return win32gui.WindowFromPoint((x, y))

def is_kbond_chat_history(hwnd):
    """Checks if the hwnd is a ReadOnly RichEdit inside a KBond chat window."""
    try:
        cls = win32gui.GetClassName(hwnd)
        if "RichEdit" not in cls:
            return False
        
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if not (style & win32con.ES_READONLY):
            return False
            
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
        result = win32gui.SendMessage(hwnd, win32con.EM_GETSEL, 0, 0)
        start = result & 0xFFFF
        end = (result >> 16) & 0xFFFF
        return start != end
    except:
        return False

def get_sentence_at_pos(hwnd, x, y):
    """Extracts the specific line (sentence) at the screen coordinates (x, y)."""
    try:
        # Convert screen coordinates to client coordinates
        point = win32gui.ScreenToClient(hwnd, (x, y))
        
        # EM_CHARFROMPOS for RichEdit: pack x,y into lParam
        lParam = (point[1] << 16) | (point[0] & 0xFFFF)
        char_idx = win32gui.SendMessage(hwnd, win32con.EM_CHARFROMPOS, 0, lParam)
        
        # EM_LINEFROMCHAR: Gets line index from character index
        line_idx = win32gui.SendMessage(hwnd, win32con.EM_LINEFROMCHAR, char_idx, 0)
        
        # EM_LINEINDEX: Gets the character index of the first character of the line
        line_start = win32gui.SendMessage(hwnd, win32con.EM_LINEINDEX, line_idx, 0)
        
        # EM_LINELENGTH: Gets length of the line
        line_len = win32gui.SendMessage(hwnd, win32con.EM_LINELENGTH, line_start, 0)
        if line_len <= 0:
            return ""
        
        # Get all text and extract the line
        all_text = get_all_text(hwnd)
        if all_text and line_start >= 0:
            lines = all_text.splitlines()
            if 0 <= line_idx < len(lines):
                return lines[line_idx]
        
        return ""
    except Exception as e:
        print(f"[DEBUG] get_sentence_at_pos error: {e}")
        return ""

def get_all_text(hwnd):
    """Extracts all text from the RichEdit control using win32gui."""
    try:
        length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
        print(f"[DEBUG] get_all_text: WM_GETTEXTLENGTH returned {length}")
        
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buffer)
            result = buffer.value
            print(f"[DEBUG] get_all_text: Got {len(result)} chars")
            return result
        return ""
    except Exception as e:
        print(f"[DEBUG] get_all_text error: {e}")
        return ""
