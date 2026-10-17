import json
import urllib.request
from core.database import Database


class IMDbSync:

    def __init__(self, db: Database, tmdb_api_key: str = None, omdb_api_key: str = None):
        self.db = db
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key

    def test_connection(self) -> bool:
        """Tests connectivity to the TMDB or OMDb service using configured keys."""
        if self.tmdb_api_key:
            try:
                url = f"https://api.themoviedb.org/3/configuration?api_key={self.tmdb_api_key}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as response:
                    return response.status == 200
            except Exception:
                pass

        if self.omdb_api_key:
            try:
                url = f"https://www.omdbapi.com/?apikey={self.omdb_api_key}&t=test"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read().decode())
                    return "Response" in data
            except Exception:
                pass

        return False

    def fetch_series_metadata(self, show_name: str):
        # Future implementation for pulling show metadata, seasons, and episodes
        pass

    def compute_missing_episodes(self, series_id: int):
        # Future implementation for comparing local media items against official episode lists
        pass
      
