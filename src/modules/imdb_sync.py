import json
import urllib.parse
import urllib.request
from core.database import Database


class IMDbSync:

    def __init__(self, db: Database, tmdb_api_key: str = None, omdb_api_key: str = None):
        self.db = db
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key

    def test_connection(self) -> bool:
        """Tests connectivity to TMDB or OMDb using configured API keys."""
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

    def sync_series(self, show_name: str) -> int:
        """Searches for a TV show via TMDB, fetches its metadata/seasons, and saves to DB."""
        if not self.tmdb_api_key:
            return 0

        try:
            # 1. Search TV Show ID
            encoded_show = urllib.parse.quote(show_name)
            search_url = f"https://api.themoviedb.org/3/search/tv?api_key={self.tmdb_api_key}&query={encoded_show}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                results = data.get("results", [])
                if not results:
                    return 0
                show_info = results[0]
                tv_id = show_info["id"]
                title = show_info.get("name")
                overview = show_info.get("overview")
                first_air_date = show_info.get("first_air_date")
                release_year = int(first_air_date[:4]) if first_air_date and len(first_air_date) >= 4 else None

            # 2. Get Detailed Show Info & Seasons
            detail_url = f"https://api.themoviedb.org/3/tv/{tv_id}?api_key={self.tmdb_api_key}"
            req_detail = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_detail, timeout=5) as resp_detail:
                detail_data = json.loads(resp_detail.read().decode())
                total_seasons = detail_data.get("number_of_seasons", 0)

            # 3. Insert Series into DB
            series_data = {
                "title": title,
                "imdb_id": str(tv_id),  # Storing TMDB ID mapping for sync
                "release_year": release_year,
                "total_seasons": total_seasons,
                "overview": overview,
                "status": detail_data.get("status"),
            }
            series_id = self.db.insert_series(series_data)

            # 4. Fetch Seasons and Episodes to populate missing/expected items
            with self.db.get_connection() as conn:
                for season in detail_data.get("seasons", []):
                    s_number = season.get("season_number")
                    if s_number == 0:
                        continue  # Skip specials for standard episode checks if desired
                    
                    # Fetch episodes for this season
                    ep_url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{s_number}?api_key={self.tmdb_api_key}"
                    try:
                        req_ep = urllib.request.Request(ep_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req_ep, timeout=5) as resp_ep:
                            ep_data = json.loads(resp_ep.read().decode())
                            for ep in ep_data.get("episodes", []):
                                ep_num = ep.get("episode_number")
                                ep_title = ep.get("name")
                                air_date = ep.get("air_date")
                                overview = ep.get("overview")

                                # Check if local media item exists for this episode, otherwise log as missing
                                existing = conn.execute(
                                    "SELECT media_id FROM media_items WHERE series_id = ? AND season_number = ? AND episode_number = ?",
                                    (series_id, s_number, ep_num)
                                ).fetchone()

                                if not existing:
                                    conn.execute(
                                        """
                                        INSERT OR IGNORE INTO missing_episodes 
                                        (series_id, season_number, episode_number, episode_title, air_date, overview)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                        """,
                                        (series_id, s_number, ep_num, ep_title, air_date, overview)
                                    )
                    except Exception:
                        pass
                conn.commit()

            return series_id
        except Exception:
            return 0

    def compute_missing_episodes(self, series_id: int):
        """Returns a list of missing episodes for a given series from the database."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM missing_episodes WHERE series_id = ?", (series_id,)
            ).fetchall()
            return [dict(row) for row in rows]
            
