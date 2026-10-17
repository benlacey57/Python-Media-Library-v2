from datetime import date
import json
from pathlib import Path
import subprocess
from core.database import Database


def run_ffprobe(file_path):
    """Runs ffprobe on a file and returns JSON metadata."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except Exception:
        return None


class Analyzer:

    def __init__(self, db: Database):
        self.db = db

    def scan_directory(self, directory_path: str) -> int:
        """Scans a directory for media files, extracts metadata via ffprobe, and saves to DB."""
        base = Path(directory_path).expanduser()
        if not base.exists():
            return 0

        count = 0
        supported_exts = {".mkv", ".mp4", ".m4v", ".avi", ".mov"}

        for file_path in base.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                metadata = run_ffprobe(file_path)
                if metadata:
                    file_size_bytes = file_path.stat().st_size
                    video_codec = "unknown"
                    resolution = "Unknown"
                    audio_count = 0
                    sub_count = 0

                    for stream in metadata.get("streams", []):
                        if stream.get("codec_type") == "video":
                            video_codec = stream.get("codec_name", "unknown")
                            w = stream.get("width")
                            h = stream.get("height")
                            if w and h:
                                resolution = f"{w}x{h}"
                        elif stream.get("codec_type") == "audio":
                            audio_count += 1
                        elif stream.get("codec_type") == "subtitle":
                            sub_count += 1

                    category_id = self.db.get_or_create_category("Movie")
                    
                    item_data = {
                        "category_id": category_id,
                        "filename": file_path.name,
                        "filepath": str(file_path.absolute()),
                        "file_size_bytes": file_size_bytes,
                        "file_size_human": f"{file_size_bytes / (1024*1024):.2f} MB",
                        "container_format": file_path.suffix.lstrip("."),
                        "resolution": resolution,
                        "video_codec": video_codec,
                        "audio_track_count": audio_count,
                        "subtitle_track_count": sub_count,
                    }
                    self.db.insert_media_item(item_data)
                    count += 1
        return count
        
