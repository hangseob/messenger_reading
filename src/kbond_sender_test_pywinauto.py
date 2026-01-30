from pywinauto import Application, Desktop
import time
import sys

def send_message_pywinauto(target_title, text):
    try:
        # Find the window
        desktop = Desktop(backend="win32")
        window = desktop.window(title_re=f".*{target_title}.*", class_name="TfrmDccChat")
        
        if not window.exists():
            print(f"Error: Could not find window with title containing '{target_title}'")
            return False
            
        print(f"Found window: {window.window_text()}")
        
        # Bring to front (might be needed for typing)
        window.set_focus()
        time.sleep(0.5)
        
        # Find the input field (not readonly)
        # In Delphi RichEdit, sometimes descendants works better
        input_field = None
        for child in window.descendants(control_type="Edit"):
            # Check if it's readonly. In pywinauto, we can check style.
            # ES_READONLY = 0x0800
            if not (child.get_style() & 0x0800):
                input_field = child
                break
        
        if not input_field:
            # Try TRichEdit/TJvRichEdit specifically if Edit didn't work
            for child in window.descendants():
                if "RichEdit" in child.class_name():
                    if not (child.get_style() & 0x0800):
                        input_field = child
                        break
        
        if not input_field:
            print("Error: Could not find editable input field.")
            return False
            
        print(f"Found input field: {input_field.class_name()}")
        
        # Type the text and press enter
        # set_edit_text is often better than type_keys for background-ish setting
        # but type_keys is more like real user typing
        input_field.type_keys(text + "{ENTER}", with_spaces=True)
        
        print(f"Sent message: '{text}' to '{target_title}'")
        return True
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    target = "정민후"
    message = "자동메세지 테스트입니다"
    send_message_pywinauto(target, message)
