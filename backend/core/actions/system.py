# core/actions/system.py
import os
import subprocess

class SystemActions:
    """Muse's hands - System level controls for macOS"""

    def execute_applescript(self, script: str):
        """Helper to run AppleScript commands"""
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except Exception as e:
            print(f"AppleScript Error: {e}")
            return False

    def set_volume(self, level: int):
        """Set system volume (0-100)"""
        return self.execute_applescript(f"set volume output volume {level}")

    def toggle_dark_mode(self):
        """Toggle macOS Dark Mode"""
        script = 'tell application "System Events" to tell appearance preferences to set dark mode to not dark mode'
        return self.execute_applescript(script)

    def sleep_mac(self):
        """Put Mac to sleep"""
        return self.execute_applescript('tell application "System Events" to sleep')

    def empty_trash(self):
        """Empty the trash bin"""
        return self.execute_applescript('tell application "Finder" to empty trash')

system_actions = SystemActions()