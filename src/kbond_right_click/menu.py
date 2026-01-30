"""
KBond Custom Right-Click Menu - Tkinter 버전 (메인 스레드 실행)

메인 스레드에서 실행되므로:
- Tcl_AsyncDelete 에러 없음
- 스레드 안전
- 더미 창이나 다른 창 참조 필요 없음
"""

import tkinter as tk
import pyperclip
import win32gui
import win32con
import time

def ts():
    """밀리초 타임스탬프 반환"""
    return time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"

def close_popup_menus():
    """시스템에 열린 팝업 메뉴(#32768)를 닫습니다."""
    closed_count = 0
    def enum_callback(hwnd, _):
        nonlocal closed_count
        try:
            cls = win32gui.GetClassName(hwnd)
            if cls == "#32768":
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed_count += 1
        except:
            pass
        return True
    try:
        win32gui.EnumWindows(enum_callback, None)
    except:
        pass
    
    if closed_count > 0:
        print(f"[{ts()}] close_popup_menus: closed {closed_count} popup(s)")
    return closed_count

def show_tkinter_menu(x, y, sentence_text, all_text):
    """
    Tkinter를 사용하여 팝업 메뉴를 표시합니다.
    ⚠️ 반드시 메인 스레드에서 호출해야 합니다!
    """
    print(f"[{ts()}] show_tkinter_menu called. pos=({x}, {y})")
    print(f"[{ts()}] sentence_len={len(sentence_text) if sentence_text else 0}, all_text_len={len(all_text) if all_text else 0}")
    
    # KBond의 기본 메뉴를 닫음
    close_popup_menus()
    time.sleep(0.05)
    
    root = None
    menu_closed = [False]
    
    def close_menu(event=None):
        if menu_closed[0]:
            return
        menu_closed[0] = True
        print(f"[{ts()}] Closing menu...")
        if root:
            try:
                root.quit()
                root.destroy()
            except:
                pass

    def copy_sentence():
        print(f"[{ts()}] copy_sentence called.")
        if sentence_text:
            pyperclip.copy(sentence_text)
            print(f"[{ts()}] Copied sentence: {sentence_text[:50]}...")
        else:
            print(f"[{ts()}] WARN: No sentence to copy.")
        close_menu()

    def copy_all():
        print(f"[{ts()}] copy_all called.")
        if all_text:
            pyperclip.copy(all_text)
            print(f"[{ts()}] Copied all text ({len(all_text)} chars).")
        else:
            print(f"[{ts()}] WARN: No text to copy.")
        close_menu()

    try:
        print(f"[{ts()}] Creating Tkinter menu...")
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        
        # 작은 투명 윈도우를 만들어 포커스를 받을 수 있게 함
        root.geometry(f"1x1+{x}+{y}")
        root.deiconify()
        root.focus_force()

        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="문장복사", command=copy_sentence)
        menu.add_command(label="모두복사", command=copy_all)
        menu.add_separator()
        menu.add_command(label="닫기", command=close_menu)
        
        # 메뉴 외부 클릭 시 닫기
        root.bind("<Button-1>", close_menu)
        root.bind("<Button-3>", close_menu)
        root.bind("<Escape>", close_menu)
        
        print(f"[{ts()}] Posting menu at ({x}, {y})...")
        menu.post(x, y)
        
        # 메뉴가 사라지면 종료하도록 폴링
        def check_menu():
            if menu_closed[0]:
                return
            try:
                if not menu or not menu.winfo_exists():
                    print(f"[{ts()}] Menu no longer exists, closing...")
                    close_menu()
                else:
                    root.after(100, check_menu)
            except:
                close_menu()
        
        root.after(100, check_menu)
        
        print(f"[{ts()}] Entering Tkinter mainloop...")
        root.mainloop()
        print(f"[{ts()}] Tkinter mainloop exited.")
        
    except Exception as e:
        print(f"[{ts()}] ERROR in show_tkinter_menu: {e}")
        if root:
            try:
                root.destroy()
            except:
                pass
