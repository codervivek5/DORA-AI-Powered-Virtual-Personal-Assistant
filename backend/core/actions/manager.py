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
            "OPEN_APP", "SEARCH_GOOGLE", "PLAY_YOUTUBE",
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
        # Uses a Non-Greedy capture with a Lookahead (?=...) to ensure 
        # parameters don't accidentally swallow the 'RESPONSE:' tag.
        action_pattern = r"ACTION:\s*(\w+)(?:\s*PARAM:\s*(.*?))?(?=\s*RESPONSE:|$)"
        matches = re.findall(action_pattern, raw_text, re.IGNORECASE | re.DOTALL)

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
            else:
                print(f"⚠️ Ignored unsupported action: {action_name}")

        # 4. Extract Final Spoken Response
        # We look for the RESPONSE: tag. If missing, we clean the raw text.
        response_match = re.search(r"RESPONSE:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)

        if response_match:
            return response_match.group(1).strip()

        # If no tag found, strip out the ACTION/PARAM blocks to get clean text
        clean_text = re.sub(r"(ACTION|PARAM):.*?(?=\s*RESPONSE:|$)", "", raw_text, flags=re.IGNORECASE | re.DOTALL)
        return clean_text.strip() if clean_text.strip() else fallback_response

    def _dispatch_action(self, name: str, param: str):
        """Routes the validated action to the correct submodule."""
        if name == "OPEN_APP":
            app_actions.open_app(param)

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
        "raw": "ACTION: OPEN_APP PARAM: Notes RESPONSE: I've opened your Notes app.",
        "response": "I've opened your Notes app."
    }
    print(f"Test Result: {test_manager.parse_and_execute(test_json)}")