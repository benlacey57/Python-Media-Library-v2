from datetime import datetime
from pathlib import Path
import subprocess
from core.database import Database


class Optimizer:

    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or {
            "tv_settings": {
                "preferred_video_codec": "libx265",
                "inefficient_codecs": ["h264", "mpeg4", "mpeg2video", "wmv3", "vc1"],
            },
            "movie_settings": {
                "preferred_video_codec": "libx265",
                "inefficient_codecs": ["h264", "mpeg4", "mpeg2video", "wmv3", "vc1"],
            },
        }

    def optimize_media_items(self):
        """Scans pending items in the database and applies FFmpeg optimizations."""
        executed_actions = []
        items = self.db.get_media_items()

        with self.db.get_connection() as conn:
            for item in items:
                media_id = item["media_id"]
                filepath = Path(item["filepath"])
                if not filepath.exists():
                    continue

                video_codec = item["video_codec"]
                category = "TV Show" if item["series_id"] else "Movie"
                settings = self.config["tv_settings"] if category == "TV Show" else self.config["movie_settings"]
                inefficient_codecs = settings["inefficient_codecs"]
                target_codec = settings["preferred_video_codec"]

                needs_transcode = video_codec in inefficient_codecs
                action_type = "TRANSCODE_VIDEO" if needs_transcode else "STRIP_NON_ENG_TRACKS"

                out_path = filepath.with_name(f"optimized_{filepath.name}")
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(filepath),
                    "-map",
                    "0:v",
                    "-map",
                    "0:a:m:language:eng?",
                    "-map",
                    "0:s:m:language:eng?",
                ]

                if needs_transcode:
                    cmd.extend(["-c:v", target_codec, "-crf", "28", "-preset", "medium"])
                else:
                    cmd.extend(["-c:v", "copy"])

                cmd.extend(["-c:a", "copy", "-c:s", "copy", str(out_path)])

                try:
                    subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    
                    # Replace original file with optimized version
                    filepath.unlink()
                    out_path.rename(filepath)

                    status = "Success"
                    details = f"Optimized using {target_codec}" if needs_transcode else "Stripped non-English tracks"

                except Exception as e:
                    status = "Failed"
                    details = str(e)
                    if out_path.exists():
                        out_path.unlink()

                # Log to file_optimizations table
                conn.execute(
                    """
                    INSERT INTO file_optimizations (media_id, action_type, status, details, executed_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (media_id, action_type, status, details, datetime.now().isoformat())
                )
                conn.commit()

                executed_actions.append({
                    "media_id": media_id,
                    "action_type": action_type,
                    "status": status,
                    "details": details,
                })

        return executed_actions
      
