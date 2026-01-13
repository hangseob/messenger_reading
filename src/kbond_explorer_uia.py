from pywinauto import Desktop
import time

def explore_with_uia():
    print("Exploring with UIA...")
    try:
        desktop = Desktop(backend="uia")
        # Find windows with KBond related titles
        windows = desktop.windows()
        for win in windows:
            title = win.window_text()
            if any(name in title for name in ["정민후", "조인목", "도진용"]):
                print(f"\nFound Window: {title}")
                # Try to find all text elements
                try:
                    texts = win.descendants(control_type="Text")
                    print(f"  Found {len(texts)} Text elements.")
                    for t in texts[:20]: # Show first 20
                        print(f"    Text: '{t.window_text()}'")
                    
                    edits = win.descendants(control_type="Edit")
                    print(f"  Found {len(edits)} Edit elements.")
                    for e in edits:
                        print(f"    Edit: '{e.get_value()}'")

                    document = win.descendants(control_type="Document")
                    print(f"  Found {len(document)} Document elements.")
                    for d in document:
                        print(f"    Document Text: '{d.get_value()}'")
                except Exception as e:
                    print(f"    Error getting descendants: {e}")
    except Exception as e:
        print(f"UIA Error: {e}")

if __name__ == "__main__":
    explore_with_uia()
