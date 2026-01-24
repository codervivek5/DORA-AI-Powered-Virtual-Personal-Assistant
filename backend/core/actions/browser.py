# core/actions/browser.py
import webbrowser
import urllib.parse

class BrowserActions:
    """Web browsing actions for Muskan"""

    def google_search(self, query: str):
        """Search Google in the default browser"""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return True

    def play_youtube(self, topic: str):
        """Search and play a video on YouTube"""
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(topic)}"
        webbrowser.open(url)
        return True

browser_actions = BrowserActions()