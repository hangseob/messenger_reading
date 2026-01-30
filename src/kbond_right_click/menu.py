"""
KBond Custom Right-Click Menu - Win32 TrackPopupMenu 버전

이전 Tkinter 버전의 문제점:
1. Tcl_AsyncDelete 에러: "async handler deleted by the wrong thread"
2. Native 메뉴 겹침 문제
3. 스레드 안전성 부족

Win32 TrackPopupMenu 버전의 장점:
- 스레드 안전 (어느 스레드에서든 호출 가능)
- 네이티브 Windows 메뉴 (KBond와 같은 방식)
- 자동으로 포커스 잃으면 닫힘
"""

import win32gui
import win32con
import win32api
import pyperclip
import ctypes
import time

user32 = ctypes.windll.user32

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
                # WM_CLOSE: 메뉴를 직접 닫음
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

# 메뉴 아이템 ID
MENU_COPY_SENTENCE = 1
MENU_COPY_ALL = 2
MENU_CLOSE = 3

def show_custom_menu(x, y, sentence_text, all_text):
    """
    Win32 TrackPopupMenu를 사용하여 네이티브 팝업 메뉴를 표시합니다.
    """
    print(f"[{ts()}] show_custom_menu called. pos=({x}, {y})")
    print(f"[{ts()}] sentence_len={len(sentence_text) if sentence_text else 0}, all_text_len={len(all_text) if all_text else 0}")
    
    # KBond의 기본 메뉴를 닫음
    close_popup_menus()
    time.sleep(0.1)  # 메뉴가 완전히 닫히도록 대기
    
    try:
        # 팝업 메뉴 생성
        menu = win32gui.CreatePopupMenu()
        
        # 메뉴 아이템 추가
        win32gui.InsertMenu(menu, 0, win32con.MF_BYPOSITION | win32con.MF_STRING, 
                           MENU_COPY_SENTENCE, "문장복사")
        win32gui.InsertMenu(menu, 1, win32con.MF_BYPOSITION | win32con.MF_STRING, 
                           MENU_COPY_ALL, "모두복사")
        win32gui.InsertMenu(menu, 2, win32con.MF_BYPOSITION | win32con.MF_SEPARATOR, 0, "")
        win32gui.InsertMenu(menu, 3, win32con.MF_BYPOSITION | win32con.MF_STRING, 
                           MENU_CLOSE, "닫기")
        
        print(f"[{ts()}] Win32 menu created")
        
        # TPM_RETURNCMD: 선택된 메뉴 ID 반환 (WM_COMMAND 대신)
        # TPM_NONOTIFY: 알림 메시지 보내지 않음
        cmd = user32.TrackPopupMenu(
            menu,
            win32con.TPM_RETURNCMD | win32con.TPM_NONOTIFY | win32con.TPM_LEFTBUTTON,
            x, y, 0, 
            win32gui.GetDesktopWindow(),  # 데스크탑 창을 소유자로 사용
            None
        )
        
        print(f"[{ts()}] Menu selection: {cmd}")
        
        # 메뉴 선택 처리
        if cmd == MENU_COPY_SENTENCE:
            if sentence_text:
                pyperclip.copy(sentence_text)
                print(f"[{ts()}] Copied sentence: {sentence_text[:50]}...")
            else:
                print(f"[{ts()}] WARN: No sentence to copy")
        elif cmd == MENU_COPY_ALL:
            if all_text:
                pyperclip.copy(all_text)
                print(f"[{ts()}] Copied all text ({len(all_text)} chars)")
            else:
                print(f"[{ts()}] WARN: No text to copy")
        elif cmd == MENU_CLOSE or cmd == 0:
            print(f"[{ts()}] Menu closed (cmd={cmd})")
        
        # 메뉴 정리
        win32gui.DestroyMenu(menu)
        print(f"[{ts()}] Menu destroyed, done.")
        
    except Exception as e:
        print(f"[{ts()}] ERROR in show_custom_menu: {e}")
