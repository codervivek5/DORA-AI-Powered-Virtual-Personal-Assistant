# core/actions/whatsapp.py
import subprocess
import urllib.parse

class WhatsappActions:
    """Muse's voice - Communication controls for macOS"""

    def send_whatsapp_message(self, person_name: str, message: str):
        """
        Sends a WhatsApp message using macOS AppleScript and WhatsApp Desktop.
        Logic: Open WhatsApp -> Search for person -> Type message -> Send.
        """
        print(f"📱 WhatsApp: Sending to '{person_name}' message: '{message}'")
        
        # AppleScript to automate WhatsApp Desktop
        script = f'''
        tell application "WhatsApp" to activate
        delay 1
        tell application "System Events"
            -- Command+F to search
            keystroke "f" using {{command down}}
            delay 0.5
            -- Type person name
            keystroke "{person_name}"
            delay 1
            -- Select first result
            key code 36 -- Enter
            delay 0.5
            -- Type message
            keystroke "{message}"
            delay 0.5
            -- Send message
            key code 36 -- Enter
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except Exception as e:
            print(f"❌ WhatsApp Action Error: {e}")
            return False

whatsapp_actions = WhatsappActions()
