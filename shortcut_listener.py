import subprocess
from pynput import keyboard

# Important: Make sure the job_tracker.py file is in the same directory
try:
    from job_tracker import EnhancedJobTracker
except ImportError:
    print("Error: Could not import EnhancedJobTracker.")
    print("Please make sure 'job_tracker.py' is in the same directory as this script.")
    exit(1)

# --- Configuration ---
# The keyboard shortcut to trigger the capture.
# Format uses '+' for modifiers (cmd, alt, ctrl, shift)
HOTKEY = '<cmd>+<shift>+k'

# --- Helper Functions ---

def get_active_app_name():
    """Returns the name of the frontmost application on macOS."""
    try:
        script = 'tell application "System Events" to get name of first process whose frontmost is true'
        process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr:
            print(f"Error getting active app: {stderr.decode('utf-8').strip()}")
            return None
        return stdout.decode('utf-8').strip()
    except Exception as e:
        print(f"Could not get active app name: {e}")
        return None

def get_chrome_url():
    """Returns the URL of the active tab in Google Chrome on macOS using AppleScript."""
    try:
        script = 'tell application "Google Chrome" to get URL of active tab of first window'
        process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode('utf-8').strip()
            print(f"AppleScript Error: {error_message}")
            if "access" in error_message.lower():
                 print("\n--- PERMISSION REQUIRED ---")
                 print("This script needs permission to control Google Chrome.")
                 print("Please go to System Settings > Privacy & Security > Automation.")
                 print("Find your Terminal (or code editor) in the list and ensure 'Google Chrome' is checked ON.")
                 print("---------------------------\n")
            return None
            
        return stdout.decode('utf-8').strip()
    except FileNotFoundError:
        print("Error: 'osascript' command not found. This script is designed for macOS.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting the Chrome URL: {e}")
        return None

def on_hotkey_press():
    """The main function called when the hotkey is detected."""
    print(f"\nHotkey '{HOTKEY}' detected!")
    
    active_app = get_active_app_name()
    if not active_app:
        return
        
    print(f"Active application: {active_app}")

    # Check if the active application is Google Chrome
    if "Google Chrome" not in active_app:
        print("Chrome is not the active application. Aborting.")
        return

    # 1. Get the URL from the active Chrome tab
    print("Querying Chrome for the active tab's URL...")
    url = get_chrome_url()
    
    if not url:
        print("Failed to get URL from Chrome. Aborting.")
        return
    
    print(f"Found URL: {url}")

    # 2. Add the job using the job_tracker's existing URL processing logic
    print("Processing URL to extract job information...")
    tracker = EnhancedJobTracker()
    success = tracker.add_job_from_url(url)

    if success:
        print("="*40)
        print("🎉 Successfully added new job from Chrome URL! 🎉")
        print("="*40)
    else:
        print("="*40)
        print("🔴 Failed to add new job. Check for duplicates or errors above. 🔴")
        print("="*40)

def main():
    """Sets up and starts the hotkey listener."""
    print("--- Job Shortcut Listener Started ---")
    print(f"Press '{HOTKEY}' when Google Chrome is active to capture a job posting.")
    print("Press Ctrl+C in this terminal to stop the listener.")

    # Set up and start the hotkey listener
    try:
        with keyboard.GlobalHotKeys({HOTKEY: on_hotkey_press}) as h:
            h.join()
    except Exception as e:
        print(f"\nAn error occurred starting the listener: {e}")
        print("This might be a permissions issue. See the setup instructions.")

if __name__ == "__main__":
    main()
