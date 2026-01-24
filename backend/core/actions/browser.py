# core/actions/browser.py
import webbrowser

class BrowserActions:
    def open_url(self, url: str):
        webbrowser.open(url)
        return f"Opening {url}"

    def search_google(self, query: str):
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Searching Google for {query}"

    def play_on_youtube(self, search_term: str):
        url = f"https://www.youtube.com/results?search_query={search_term}"
        webbrowser.open(url)
        return f"Looking for {search_term} on YouTube"

browser_actions = BrowserActions()