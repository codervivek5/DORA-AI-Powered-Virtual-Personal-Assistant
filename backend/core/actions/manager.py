import re
import logging
from typing import Union, Dict, Any

# Import specialized action modules
from core.actions.apps import app_actions
from core.actions.browser import browser_actions
from core.actions.system import system_actions
from core.actions.whatsapp import whatsapp_actions
from core.actions.weather import weather_actions


class ActionManager:
    """
    Central dispatcher for Muse AI actions.
    Optimized for high-reliability parsing and error-resilient execution.
    """

    def __init__(self):
        # Define supported actions for validation
        self.supported_actions = {
            "OPEN_APP", "CLOSE_APP", "SEARCH_GOOGLE", "PLAY_YOUTUBE",
            "SET_VOLUME", "EMPTY_TRASH", "SEND_WHATSAPP",
            "GET_WEATHER"
        }

    def parse_and_execute(self, ai_input: Union[str, Dict[str, Any]]) -> str:
        """
        Main entry point. Handles both raw strings and Brain dictionary objects.
        Returns the final text that should be spoken/displayed to the user.
        """
        # 1. Type Safety: Extract the 'raw' string if input is a dictionary
        if isinstance(ai_input, dict):
            raw_text = ai_input.get("raw", "")
            # If the brain already extracted a friendly response, we'll keep it as a backup
            fallback_response = ai_input.get("response", "")
        else:
            raw_text = str(ai_input)
            fallback_response = ""

        print(f"DEBUG: Processing Input: {repr(raw_text)}")

        # 2. Optimized Regex Parsing
        # Try different formats for maximum reliability
        
        # Format 1: Strict Prompt Style (ACTION: ... PARAM: ...)
        strict_pattern = r"ACTION:\s*([\w_]+).*?PARAM:\s*(.*?)(?=\s*RESPONSE:|$)"
        matches = re.findall(strict_pattern, raw_text, re.IGNORECASE | re.DOTALL)

        # Format 2: Direct Style (ACTION_NAME: Parameter) - sometimes AI does this
        if not matches:
            for action_name in self.supported_actions:
                pattern = rf"{action_name}:\s*(.*?)(?=\s*RESPONSE:|$)"
                loose_match = re.search(pattern, raw_text, re.IGNORECASE)
                if loose_match:
                    matches.append((action_name, loose_match.group(1).strip()))

        # Format 3: Keyword Fallback (ULTRA-ROBUST)
        # If still no matches, look for keywords in the Hindi response
        if not matches:
            # Common app names to look for
            common_apps = ["WhatsApp", "Chrome", "Google Chrome", "Safari", "Notes", "Finder", "Terminal"]
            for app in common_apps:
                if app.lower() in raw_text.lower():
                    if any(kw in raw_text for kw in ["खोल", "open", "लाओ"]):
                        matches.append(("OPEN_APP", app))
                        break
                    elif any(kw in raw_text for kw in ["बंद", "close", "quit"]):
                        matches.append(("CLOSE_APP", app))
                        break

        # 3. Execution Loop
        for action_name, action_param in matches:
            action_name = action_name.strip().upper()
            action_param = action_param.strip()

            if action_name in self.supported_actions:
                print(f"🛠️ Executing: {action_name} | Param: {action_param}")
                try:
                    self._dispatch_action(action_name, action_param)
                except Exception as e:
                    print(f"❌ Execution Failure ({action_name}): {e}")

        # 4. Extract Final Spoken Response
        response_match = re.search(r"RESPONSE:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)
        
        if response_match:
            final_text = response_match.group(1).strip()
        else:
            # If no RESPONSE tag, check if we triggered actions.
            # If so, generate a friendly default confirmation.
            if matches:
                action_name, action_param = matches[0]
                if action_name == "OPEN_APP":
                    final_text = f"{action_param} खोल रही हूँ 😊"
                elif action_name == "CLOSE_APP":
                    final_text = f"{action_param} बंद कर रही हूँ 😊"
                elif action_name == "SEARCH_GOOGLE":
                    final_text = f"Google पर {action_param} search कर रही हूँ 😊"
                elif action_name == "PLAY_YOUTUBE":
                    final_text = f"YouTube पर {action_param} चला रही हूँ 😊"
                elif action_name == "SEND_WHATSAPP":
                    contact = action_param.split("|")[0].strip() if "|" in action_param else action_param
                    final_text = f"{contact} को संदेश भेज रही हूँ 😊"
                else:
                    final_text = fallback_response
            else:
                final_text = fallback_response

        # Final Cleanup: Deep strip ANY technical tags from the final speech string
        # Strip Action: Param formats
        for action in self.supported_actions:
            final_text = re.sub(rf"{action}:\s*", "", final_text, flags=re.IGNORECASE).strip()
        
        # Strip standard tags
        final_text = re.sub(r"(ACTION|PARAM|RESPONSE):\s*", "", final_text, flags=re.IGNORECASE).strip()
        
        # If after all cleanup it's still empty or looks technical, use a safe default
        if not final_text or any(tag in final_text.upper() for tag in self.supported_actions):
            return "ठीक है 😊"

        return final_text

    def _dispatch_action(self, name: str, param: str):
        """Routes the validated action to the correct submodule."""
        if name == "OPEN_APP":
            app_actions.open_app(param)
        elif name == "CLOSE_APP":
            app_actions.close_app(param)

        elif name == "SEARCH_GOOGLE":
            browser_actions.google_search(param)

        elif name == "PLAY_YOUTUBE":
            browser_actions.play_youtube(param)
        elif name == "GET_WEATHER":
            weather_actions.get_weather(param)

        elif name == "SET_VOLUME":
            # Extract just the numbers (handles "50%" or "to 50")
            vol_match = re.search(r"\d+", param)
            if vol_match:
                system_actions.set_volume(int(vol_match.group()))

        elif name == "EMPTY_TRASH":
            system_actions.empty_trash()

        elif name == "SEND_WHATSAPP":
            # Expected format: "Recipient Name | Message text"
            if "|" in param:
                contact, message = param.split("|", 1)
                whatsapp_actions.send_whatsapp_message(contact.strip(), message.strip())
            else:
                print(f"⚠️ WhatsApp Format Error. Expected '|' separator in: {param}")


# Global instance for easy import
action_manager = ActionManager()

if __name__ == "__main__":
    # Test block to verify the logic
    test_manager = ActionManager()
    test_json = {
        "raw": "ACTION: OPEN_APP\nPARAM: Notes\nRESPONSE: कर दिया 😊",
        "response": "कर दिया 😊"
    }
    print(f"Test Result: {test_manager.parse_and_execute(test_json)}")