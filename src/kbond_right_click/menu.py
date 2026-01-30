"""
KBond Custom Right-Click Menu - Tkinter 버전

⚠️ 알려진 문제점 (2026-01-30):
1. Tcl_AsyncDelete 에러: "async handler deleted by the wrong thread"
   - 원인: Tkinter는 메인 스레드에서만 실행 가능한데, 현재 별도 스레드에서 호출됨
   - 증상: 여러 번 우클릭 후 Python 프로그램 crash
   
2. Native 메뉴 겹침 문제:
   - KBond의 기본 우클릭 메뉴가 커스텀 메뉴 아래에 겹쳐서 표시됨
   - close_popup_menus()가 완전히 동작하지 않음
   
3. 스레드 안전성 부족:
   - root.mainloop()이 별도 스레드에서 실행되어 불안정
   - 메뉴 종료 시 리소스 정리가 완전하지 않을 수 있음

→ 해결책: Win32 TrackPopupMenu API로 전환 필요
"""

import tkinter as tk
import pyperclip
import win32gui
import win32con

def close_popup_menus():
    """시스템에 열린 팝업 메뉴(#32768)를 모두 닫습니다."""
    closed_count = 0
    def enum_callback(hwnd, _):
        nonlocal closed_count
        cls = win32gui.GetClassName(hwnd)
        if cls == "#32768":
            print(f"[DEBUG] Found popup menu: HWND={hwnd}, closing...")
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            closed_count += 1
        return True
    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception as e:
        print(f"[DEBUG] EnumWindows error: {e}")
    
    print(f"[DEBUG] close_popup_menus: closed {closed_count} popup(s)")
    return closed_count

def show_custom_menu(hwnd, x, y, sentence_text, all_text):
    """Displays a custom popup menu using Tkinter with pre-fetched text."""
    print(f"[DEBUG] show_custom_menu called. pos=({x}, {y})")
    print(f"[DEBUG] Pre-fetched sentence: '{sentence_text[:50] if sentence_text else 'EMPTY'}...'")
    print(f"[DEBUG] Pre-fetched all_text length: {len(all_text) if all_text else 0} chars")
    
    # KBond의 기본 메뉴를 닫음
    close_popup_menus()
    
    root = None
    
    def copy_sentence():
        if sentence_text:
            pyperclip.copy(sentence_text)
            print(f"[INFO] Copied: {sentence_text[:50]}...")
        else:
            print("[WARN] No sentence to copy.")
        close_menu()

    def copy_all():
        if all_text:
            pyperclip.copy(all_text)
            print("[INFO] Copied all text.")
        else:
            print("[WARN] No text to copy.")
        close_menu()

    def close_menu(event=None):
        print("[DEBUG] Closing menu...")
        if root:
            root.quit()
            root.destroy()

    try:
        print("[DEBUG] Creating Tkinter menu...")
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
        
        # 메뉴가 닫히면(unpost) 종료
        def on_menu_close():
            print("[DEBUG] Menu unposted")
            close_menu()
        
        # 메뉴 외부 클릭 시 닫기
        root.bind("<Button-1>", close_menu)
        root.bind("<Button-3>", close_menu)
        root.bind("<Escape>", close_menu)
        root.bind("<FocusOut>", close_menu)
        
        print(f"[DEBUG] Posting menu at ({x}, {y})...")
        menu.post(x, y)
        
        # 메뉴가 사라지면 종료하도록 폴링
        def check_menu():
            try:
                if not menu.winfo_exists():
                    close_menu()
                else:
                    root.after(100, check_menu)
            except:
                pass
        
        root.after(100, check_menu)
        
        print("[DEBUG] Entering Tkinter mainloop...")
        root.mainloop()
        print("[DEBUG] Tkinter mainloop exited.")
        
    except Exception as e:
        print(f"[ERROR] Menu Error: {e}")
        if root:
            try:
                root.destroy()
            except:
                pass
