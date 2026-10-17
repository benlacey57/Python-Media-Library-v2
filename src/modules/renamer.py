from pathlib import Path
import re
from core.database import Database


class Renamer:

    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or {}
        # Default fallback templates if not specified in config
        self.templates = self.config.get("filename_templates", {
            "movie": "{title}.{year}.{resolution}.{video_codec}",
            "tv_show": "{series_name}.S{season:02d}E{episode:02d}.{episode_title}"
        })

    def clean_filename(self, filename: str) -> str:
        """Removes bracketed groups, release tags, and cleans excessive whitespace/dots."""
        p = Path(filename)
        stem = p.stem
        ext = p.suffix

        stem = re.sub(r"\[.*?\]|\(.*?\)", "", stem)
        stem = re.sub(r"-[a-zA-Z0-9_-]+$", "", stem)
        stem = re.sub(r"\s+", ".", stem).strip(".")
        stem = re.sub(r"\.+", ".", stem)
        
        return f"{stem}{ext}"

    def format_movie_name(self, title: str, year: int, resolution: str, video_codec: str, ext: str) -> str:
        """Formats a movie filename based on the configured template."""
        template = self.templates.get("movie", "{title}.{year}.{resolution}.{video_codec}")
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", ".")
        safe_resolution = resolution if resolution else "Unknown"
        safe_codec = video_codec if video_codec else "unknown"
        safe_year = str(year) if year else "Unknown"

        formatted = template.format(
            title=safe_title,
            year=safe_year,
            resolution=safe_resolution,
            video_codec=safe_codec
        )
        return f"{formatted}{ext}"

    def format_episode_name(self, series_name: str, season: int, episode: int, episode_title: str, ext: str) -> str:
        """Formats a TV show episode filename based on the configured template."""
        template = self.templates.get("tv_show", "{series_name}.S{season:02d}E{episode:02d}.{episode_title}")
        
        safe_series = re.sub(r'[\\/*?:"<>|]', "", series_name).replace(" ", ".")
        safe_title = re.sub(r'[\\/*?:"<>|]', "", episode_title).replace(" ", ".") if episode_title else f"Episode.{episode:02d}"

        # Support safe formatting whether episode_title is present or omitted in template
        try:
            formatted = template.format(
                series_name=safe_series,
                season=season,
                episode=episode,
                episode_title=safe_title
            )
        except KeyError:
            formatted = f"{safe_series}.S{season:02d}E{episode:02d}.{safe_title}"

        return f"{formatted}{ext}"
        
