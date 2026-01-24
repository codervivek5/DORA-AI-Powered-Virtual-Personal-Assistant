# core/brain.py
import requests
import json
from typing import Optional, List, Dict
from config.settings import settings

class MuskanBrain:
    """Main brain module for Muskan AI assistant using Ollama"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.conversation_history: List[Dict[str, str]] = []
        
        # System prompt for Muskan
        self.system_prompt = """You are Muskan, a super-intelligent AI assistant for macOS.You have the ability to control this computer. 

        If the user asks you to do something, respond in this format:
        ACTION: [action_name] PARAM: [value]
        RESPONSE: [Natural language response to the user]

        Available Actions:
        - OPEN_APP (e.g., "Safari", "Spotify")
        - SEARCH_GOOGLE (query)
        - SET_VOLUME (0-100)
        - EMPTY_TRASH
        - PLAY_YOUTUBE (topic)

        Example:
        User: "Muskan, open Safari and search for weather."
        Muskan: 
        ACTION: OPEN_APP PARAM: Safari
        ACTION: SEARCH_GOOGLE PARAM: weather
        RESPONSE: I've opened Safari and searched for the weather for you.
        """
    
    def _call_ollama(self, prompt: str, stream: bool = False) -> str:
        """Call Ollama API for text generation using chat endpoint"""
        url = f"{self.base_url}/api/chat"
        
        # Build messages with system prompt and conversation history
        messages = []
        
        # Add system prompt as first message
        messages.append({"role": "system", "content": self.system_prompt})
        
        # Add conversation history (last 10 exchanges to keep context manageable)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add current user prompt
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Please ensure Ollama is running. Install from https://ollama.ai"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama request timed out. The model might be loading.")
        except Exception as e:
            raise Exception(f"Error calling Ollama: {str(e)}")
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and generate AI response
        
        Args:
            user_message: User's input text
            
        Returns:
            AI assistant response
        """
        if not user_message or not user_message.strip():
            return "I didn't catch that. Could you please repeat?"
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Get response from Ollama
            response = self._call_ollama(user_message)
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except ConnectionError as e:
            return f"⚠️ {str(e)}"
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try again."
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []


# Global brain instance
brain = MuskanBrain()

if __name__ == "__main__":
    # Test the brain
    print("Testing Muskan Brain with Ollama...")
    
    if brain.check_ollama_connection():
        print("✅ Ollama is running!")
        models = brain.get_available_models()
        print(f"Available models: {models}")
        
        print("\n--- Testing chat ---")
        test_prompts = [
            "Hello! Who are you?",
            "Help me search for the weather on Google.",
            "Open Safari for me."
        ]
        
        for prompt in test_prompts:
            print(f"\nUser: {prompt}")
            response = brain.chat(prompt) # Changed to brain.chat as process_query is not defined
            print(f"Muskan: {response}")
    else:
        print("❌ Ollama is not running. Please start Ollama first.")
        print("Install: https://ollama.ai")
        print("Then run: ollama pull llama3.2")
