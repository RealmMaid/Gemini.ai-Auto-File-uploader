import pyautogui
import sys
import argparse
import time

def click_at_coordinates(x, y, click_duration=0.1, move_duration=0.2):
    """Moves to specified screen coordinates and clicks."""
    try:
        print(f"PYAUTOGUI_COORD_CLICKER: Moving mouse to ({x}, {y}) over {move_duration}s.")
        pyautogui.moveTo(x, y, duration=move_duration)
        time.sleep(0.1) # Brief pause after move
        print(f"PYAUTOGUI_COORD_CLICKER: Clicking at ({x}, {y}).")
        pyautogui.click(duration=click_duration)
        print(f"PYAUTOGUI_COORD_CLICKER: Click performed at ({x}, {y}).")
        return True
    except Exception as e:
        print(f"PYAUTOGUI_COORD_CLICKER_ERROR: Failed to move or click at ({x}, {y}): {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clicks at specified screen coordinates.")
    parser.add_argument("--x", type=int, required=True, help="X-coordinate to click.")
    parser.add_argument("--y", type=int, required=True, help="Y-coordinate to click.")
    
    args = parser.parse_args()

    print(f"PYAUTOGUI_COORD_CLICKER: Script started for coordinates X={args.x}, Y={args.y}.")
    
    if click_at_coordinates(args.x, args.y):
        print(f"PYAUTOGUI_COORD_CLICKER: Action for X={args.x}, Y={args.y} should have been performed.")
        sys.exit(0) # Exit with success code
    else:
        print(f"PYAUTOGUI_COORD_CLICKER_ERROR: Could not perform action for X={args.x}, Y={args.y}.")
        sys.exit(1) # Exit with error code
