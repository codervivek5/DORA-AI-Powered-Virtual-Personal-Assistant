# core/actions/manager.py
import re
from core.actions.apps import app_actions
from core.actions.browser import browser_actions
from core.actions.system import system_actions

class ActionManager:
    """Central dispatcher for Muskan AI actions"""

    def parse_and_execute(self, ai_response: str):
        """
        Parses ACTION: [name] PARAM: [value] blocks from AI response
        and executes corresponding methods.
        Returns the parsed RESPONSE: [text] to be spoken.
        """
        # 1. Parse all actions
        print(f"DEBUG: Processing AI Response: {repr(ai_response)}")
        
        # Case 1: ACTION: OPEN_APP PARAM: Safari
        actions = re.findall(r"ACTION:\s*(\w+)\s*(?:PARAM:\s*)?(.*?)(?=\n|RESPONSE:|$)", ai_response, re.IGNORECASE | re.DOTALL)
        
        # Case 2: OPEN_APP: Safari (Fallback for lazy LLMs)
        if not actions or not any(a[1].strip() for a in actions):
            actions = re.findall(r"(\w+):\s*(.*?)(?=\n|RESPONSE:|$)", ai_response, re.IGNORECASE)
            
        print(f"DEBUG: Initial matches found: {actions}")
        
        # Filter to only allow supported actions to avoid picking up RESPONSE:
        supported = ["OPEN_APP", "SEARCH_GOOGLE", "PLAY_YOUTUBE", "SET_VOLUME", "EMPTY_TRASH"]
        final_actions = []
        
        # Add those from regex
        for action_name, action_param in actions:
            if action_name.upper() in supported:
                final_actions.append((action_name, action_param))
        
        # Fallback: Check for single-word supported actions on their own lines
        if not final_actions:
            for line in ai_response.split('\n'):
                word = line.strip().upper()
                if word in supported:
                    final_actions.append((word, ""))
                    print(f"DEBUG: Found single-word action fallback: {word}")
            
        for action_name, action_param in final_actions:
            action_name = action_name.strip().upper()
            action_param = action_param.strip()
            
            print(f"🛠️ Executing Action: {action_name} with Param: {action_param}")
            
            try:
                if action_name == "OPEN_APP":
                    app_actions.open_app(action_param)
                elif action_name == "SEARCH_GOOGLE":
                    browser_actions.google_search(action_param)
                elif action_name == "PLAY_YOUTUBE":
                    browser_actions.play_youtube(action_param)
                elif action_name == "SET_VOLUME":
                    system_actions.set_volume(int(action_param))
                elif action_name == "EMPTY_TRASH":
                    system_actions.empty_trash()
            except Exception as e:
                print(f"❌ Action Execution Error ({action_name}): {e}")

        # 2. Extract and return the natural language response
        response_match = re.search(r"RESPONSE:\s*(.*)", ai_response, re.IGNORECASE | re.DOTALL)
        if response_match:
            return response_match.group(1).strip()
        
        # Fallback if no RESPONSE tag but text exists
        clean_text = re.sub(r"ACTION:.*?\n", "", ai_response, flags=re.IGNORECASE | re.DOTALL).strip()
        return clean_text

action_manager = ActionManager()
