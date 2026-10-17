from pathlib import Path
import re
from core.database import Database


class Renamer:

    def __init__(self, db: Database, imdb_sync=None):
        self.db = db
        self.imdb_sync = imdb_sync

    def clean_filename(self, filename: str) -> str:
        """Removes bracketed groups, release tags, and cleans excessive whitespace."""
        p = Path(filename)
        stem = p.stem
        ext = p.suffix

        # Remove common bracketed tags like [1080p], (HEVC), etc.
        stem = re.sub(r"\[.*?\]|\(.*?\)", "", stem)
        # Replace dots/underscores with spaces for cleaner processing if desired, or keep structure
        stem = re.sub(r"\s+", " ", stem).strip()
        
        return f"{stem}{ext}"

    def format_episode_name(self, series_name: str, season: int, episode: int, episode_title: str, ext: str) -> str:
        """Formats a standard TV show episode filename."""
        safe_series = re.sub(r'[\\/*?:"<>|]', "", series_name)
        safe_title = re.sub(r'[\\/*?:"<>|]', "", episode_title) if episode_title else ""
        
        season_ep = f"S{season:02d}E{episode:02d}"
        if safe_title:
            return f"{safe_series}.{season_ep}.{safe_title}{ext}"
        return f"{safe_series}.{season_ep}{ext}"

    def rename_file(self, file_path: Path, new_name: str) -> Path:
        """Renames a physical file on disk and updates the database entry."""
        target_path = file_path.with_name(new_name)
        if file_path.exists() and not target_path.exists():
            file_path.rename(target_path)
            
            # Update database if connected
            if self.db:
                with self.db.get_connection() as conn:
                    conn.execute(
                        "UPDATE media_items SET filename = ?, filepath = ?, naming_status = 'Renamed' WHERE filepath = ?",
                        (new_name, str(target_path.absolute()), str(file_path.absolute()))
                    )
                    conn.commit()
            return target_path
        return file_path
      
