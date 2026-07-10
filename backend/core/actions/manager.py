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
    Central dispatcher for Jenny AI actions.
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
        action_name = None
        action_param = None
        fallback_response = "ठीक है 😊"

        # 1. Primary Strategy: Direct JSON/Dict Reading (Highly reliable for LangGraph)
        if isinstance(ai_input, dict):
            # Read direct structural keys if populated by the brain or graph patch
            action_name = ai_input.get("action")
            action_param = ai_input.get("param")
            fallback_response = ai_input.get("response") or ai_input.get("raw") or fallback_response
            raw_text = str(ai_input.get("raw", ""))
        else:
            raw_text = str(ai_input)

        print(f"DEBUG: Processing Input Data Structure. Action: {action_name} | Param: {action_param}")

        # 2. Secondary Strategy: Regex Parsing if keys are missing but present in raw text
        matches = []
        if action_name and str(action_name).strip().lower() not in ["none", ""]:
            matches.append((action_name, action_param or ""))
        else:
            # Format 1: Strict Prompt Style (ACTION: ... PARAM: ...)
            strict_pattern = r"ACTION:\s*([\w_]+).*?PARAM:\s*(.*?)(?=\s*RESPONSE:|$)"
            matches = re.findall(strict_pattern, raw_text, re.IGNORECASE | re.DOTALL)

            # Format 2: Direct Style (ACTION_NAME: Parameter)
            if not matches:
                for act in self.supported_actions:
                    pattern = rf"{act}:\s*(.*?)(?=\s*RESPONSE:|$)"
                    loose_match = re.search(pattern, raw_text, re.IGNORECASE)
                    if loose_match:
                        matches.append((act, loose_match.group(1).strip()))

            # Format 3: Intelligent Keyword Fallback (Robust case-insensitive tracking)
            if not matches:
                clean_raw = raw_text.lower()
                if "whatsapp" in clean_raw:
                    if any(kw in clean_raw for kw in ["खोल", "open", "लाओ", "चलाओ"]):
                        matches.append(("OPEN_APP", "WhatsApp"))
                    elif any(kw in clean_raw for kw in ["बंद", "close", "quit"]):
                        matches.append(("CLOSE_APP", "WhatsApp"))

        # 3. Execution Loop
        for act_id, act_val in matches:
            if not act_id:
                continue
                
            act_id = str(act_id).strip().upper()
            act_val = str(act_val).strip()

            if act_id in self.supported_actions:
                print(f"🛠️ [DISPATCH] Executing Action: {act_id} | Param: {act_val}")
                try:
                    self._dispatch_action(act_id, act_val)
                except Exception as e:
                    print(f"❌ Execution Failure ({act_id}): {e}")

        # 4. Extract and Clean Final Spoken Response
        final_text = ""
        response_match = re.search(r"RESPONSE:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)
        
        if response_match:
            final_text = response_match.group(1).strip()
        else:
            if matches:
                # Dynamic confirmation builder based on executed action
                executed_name, executed_param = matches[0]
                if executed_name == "OPEN_APP":
                    final_text = f"{executed_param} खोल रही हूँ 😊"
                elif executed_name == "CLOSE_APP":
                    final_text = f"{executed_param} बंद कर रही हूँ 😊"
                elif executed_name == "SEARCH_GOOGLE":
                    final_text = f"Google पर {executed_param} search कर रही हूँ 😊"
                elif executed_name == "PLAY_YOUTUBE":
                    final_text = f"YouTube पर {executed_param} चला रही हूँ 😊"
                elif executed_name == "SEND_WHATSAPP":
                    contact = executed_param.split("|")[0].strip() if "|" in executed_param else executed_param
                    final_text = f"{contact} को संदेश भेज रही हूँ 😊"
                else:
                    final_text = str(fallback_response)
            else:
                final_text = str(fallback_response)

        # Deep cleanup: Strip any lingering technical tags from speech output
        for action in self.supported_actions:
            final_text = re.sub(rf"{action}:\s*", "", final_text, flags=re.IGNORECASE).strip()
        
        final_text = re.sub(r"(ACTION|PARAM|RESPONSE):\s*", "", final_text, flags=re.IGNORECASE).strip()
        
        # Safe structural fallback if text ends up empty or broken
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
            vol_match = re.search(r"\d+", param)
            if vol_match:
                system_actions.set_volume(int(vol_match.group()))

        elif name == "EMPTY_TRASH":
            system_actions.empty_trash()

        elif name == "SEND_WHATSAPP":
            if "|" in param:
                contact, message = param.split("|", 1)
                whatsapp_actions.send_whatsapp_message(contact.strip(), message.strip())
            else:
                print(f"⚠️ WhatsApp Format Error. Expected '|' separator in: {param}")


# Global instance for easy import
action_manager = ActionManager()
