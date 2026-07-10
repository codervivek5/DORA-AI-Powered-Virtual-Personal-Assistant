# core/actions/apps.py
import subprocess

class AppActions:
    """App management actions for Jenny on macOS"""

    def open_app(self, app_name: str):
        """Open a macOS application"""
        try:
            # Simple open command for macOS
            subprocess.run(["open", "-a", app_name], check=True)
            return True
        except Exception:
            # Try searching if exact name fails
            script = f'tell application "Finder" to open (first item of (every file of (path to applications folder) whose name contains "{app_name}"))'
            try:
                subprocess.run(["osascript", "-e", script], check=True)
                return True
            except:
                print(f"Failed to open app: {app_name}")
                return False

    def close_app(self, app_name: str):
        """Quit a macOS application"""
        script = f'tell application "{app_name}" to quit'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except:
            return False

app_actions = AppActions()
