from datetime import datetime
from core.database import Database
from core.audit import Audit

class MediaSeeder:
    def __init__(self, db: Database, audit: Audit = None):
        self.db = db
        self.audit = audit

    def seed(self) -> dict:
        """Seeds sample media files, audio tracks, and subtitle tracks."""
        cat_id = self.db.get_or_create_category("TV Show")
        
        media_item = {
            "category_id": cat_id,
            "series_id": 1,
            "season_number": 1,
            "episode_number": 1,
            "episode_title": "Pilot",
            "filename": "Breaking.Bad.S01E01.Pilot.mkv",
            "filepath": "/storage/tv_shows/Breaking.Bad.S01E01.Pilot.mkv",
            "file_size_bytes": 1258291200,
            "file_size_human": "1.20 GB",
            "container_format": "mkv",
            "resolution": "1920x1080",
            "video_codec": "h264",  # Inefficient codec for testing optimizer
            "audio_track_count": 2,
            "subtitle_track_count": 2,
            "analyzed_date": datetime.now().isoformat(),
            "last_modified_date": datetime.now().isoformat()
        }

        media_id = self.db.insert_media_item(media_item)

        # Seed child tracks
        with self.db.get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO audio_tracks (media_id, codec_name, language, channels, is_default)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (media_id, "aac", "eng", 6, 1),
                    (media_id, "ac3", "spa", 2, 0)
                ]
            )
            conn.executemany(
                """
                INSERT INTO subtitle_tracks (media_id, codec_name, language, is_default, is_external)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (media_id, "subrip", "eng", 1, 0),
                    (media_id, "subrip", "fra", 0, 0)
                ]
            )
            conn.commit()

        if self.audit:
            self.audit.log("Seeder", "SEED_MEDIA", "SUCCESS", f"Seeded media item ID {media_id} with tracks.")
        return {"media_id": media_id}
              
