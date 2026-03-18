import httpx
import re
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from config.settings import settings


class MuseBrain:
    """
    Muse Brain: Features persistent storage, context pruning for speed,
    and structured regex parsing for macOS automation.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        
        # Absolute path to backend/chat_history/chat_history.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.memory_file = os.path.join(base_dir, "chat_history", "chat_history.json")
        
        self.system_prompt = settings.SYSTEM_PROMPT

        # Load long-term memory
        self.conversation_history = self._load_memory()

    def _load_memory(self) -> List[Dict[str, str]]:
        """Reads chat history from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Memory load error: {e}. Starting fresh.")
                return []
        return []

    def _save_memory(self):
        """Saves chat history to disk safely."""
        try:
            # Atomic save: Write to temp first then rename to prevent corruption
            temp_file = f"{self.memory_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=4)
            os.replace(temp_file, self.memory_file)
        except Exception as e:
            print(f"⚠️ Memory save error: {e}")

    def _parse_structured_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Extracts the Action, Param, and Response components.
        Uses re.DOTALL to capture multi-line friendly responses.
        """
        # Patterns look for "ACTION: OPEN_APP" etc.
        action_match = re.search(r"ACTION:\s*(.*?)(?=\s*PARAM:|\s*RESPONSE:|$)", raw_text, re.IGNORECASE)
        param_match = re.search(r"PARAM:\s*(.*?)(?=\s*RESPONSE:|$)", raw_text, re.IGNORECASE)
        response_match = re.search(r"RESPONSE:\s*(.*)", raw_text, re.IGNORECASE | re.DOTALL)

        # Cleanup values
        action = action_match.group(1).strip() if action_match and action_match.group(1).strip() else None
        param = param_match.group(1).strip() if param_match and param_match.group(1).strip() else None

        # Fallback: If LLM forgets "RESPONSE:", use the whole raw text
        friendly_text = response_match.group(1).strip() if response_match else raw_text.strip()

        # Strip action tags from friendly text if they leaked in
        # We strip both standard tags and ALL supported action names
        standard_tags = ["ACTION", "PARAM", "RESPONSE"]
        supported_actions = ["OPEN_APP", "SEARCH_GOOGLE", "PLAY_YOUTUBE", "SET_VOLUME", "EMPTY_TRASH", "SEND_WHATSAPP", "GET_WEATHER"]
        
        for tag in standard_tags + supported_actions:
            friendly_text = re.sub(rf"{tag}:\s*", "", friendly_text, flags=re.IGNORECASE).strip()

        return {
            "action": action,
            "param": param,
            "response": friendly_text,
            "raw": raw_text
        }

    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        The main intelligence loop.
        Processes user input, updates memory, and calls Llama via Ollama.
        """
        if not user_message or not user_message.strip():
            return {"action": None, "param": None, "response": "I'm listening, tell me more."}

        # 1. Store the user's intent
        self.conversation_history.append({"role": "user", "content": user_message})

        # 2. Add dynamic context (Time/Date)
        now = datetime.now()
        timestamp_ctx = f"\n\n[CONTEXT: Today is {now.strftime('%A, %B %d, %Y %I:%M %p')}]"

        # 3. Create context window (Last 8 messages for speed + System Prompt)
        context_window = [{"role": "system", "content": self.system_prompt + timestamp_ctx}]
        context_window.extend(self.conversation_history[-8:])

        payload = {
            "model": self.model,
            "messages": context_window,
            "stream": False,
            "options": {
                "temperature": 0.6,  # Slightly lower for more reliable formatting
                "top_p": 0.9
            }
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()

                ai_content = response.json().get("message", {}).get("content", "")

                # 4. Save and return parsed data
                self.conversation_history.append({"role": "assistant", "content": ai_content})
                self._save_memory()

                return self._parse_structured_response(ai_content)

        except Exception as e:
            return {
                "action": "ERROR",
                "param": None,
                "response": f"I'm having trouble connecting to my core right now. ({str(e)})"
            }

    def clear_history(self):
        """Reset Muse's memory."""
        self.conversation_history = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        print("🧠 Memory cleared.")


# Global brain instance
brain = MuseBrain()

# --- PRODUCTION TESTING BLOCK ---

if __name__ == "__main__":
    print("--- Muse AI Brain Diagnostic ---")
    brain = MuseBrain()

    # 1. Check Connection
    try:
        with httpx.Client() as c:
            check = c.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if check.status_code == 200:
                print(f"✅ Ollama Connected. Model: {settings.OLLAMA_MODEL}")
            else:
                print("❌ Ollama responded but model not found.")
    except Exception:
        print("❌ Ollama is NOT running. Please start it first.")

    # 2. Test Conversation & Parsing
    print("\n--- Starting Test Conversation ---")
    queries = [
        "Hey Muse, how are you?",
        "What was my friends name again?"
    ]

    for q in queries:
        print(f"\nUSER: {q}")
        result = brain.chat(q)
        print(f"MUSE RESPONSE: {result['response']}")
        if result['action']:
            print(f"🛠️ ACTION TRIGGERED: {result['action']} with {result['param']}")
        print("-" * 30)

    print("\n✅ Diagnostic Complete. Check 'chat_history.json' for persistence.")