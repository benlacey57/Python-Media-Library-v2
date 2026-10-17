from datetime import datetime
import json
from pathlib import Path
import subprocess
from core.database import Database
from core.models import AudioTrackModel, MediaItemModel, SubtitleTrackModel


class Analyzer:

    def __init__(self, db: Database):
        self.db = db

    def format_size(self, size_bytes: int) -> str:
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 1024:
            return f"{size_mb / 1024:.2f} GB"
        return f"{size_mb:.2f} MB"

    def is_tv_show(self, filename: str) -> bool:
        import re
        return bool(re.search(r"(?:s\d+e\d+|\d+x\d+)", filename, re.IGNORECASE))

    def run_ffprobe(self, file_path: Path):
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

    def extract_metadata(self, file_path: Path) -> MediaItemModel | None:
        metadata = self.run_ffprobe(file_path)
        if not metadata:
            # Fallback for testing/mocking if ffprobe binary isn't present but mocked
            # Let's support graceful fallback if file stats are available
            pass

        # If metadata returned from ffprobe, parse it
        file_size_bytes = file_path.stat().st_size
        video_codec = "unknown"
        resolution = "Unknown"
        container_format = file_path.suffix.lstrip(".")
        duration_seconds = 0.0
        bitrate_kbps = None

        if metadata:
            format_info = metadata.get("format", {})
            duration_seconds = float(format_info.get("duration", 0.0))
            if "bit_rate" in format_info:
                bitrate_kbps = int(format_info["bit_rate"]) // 1000

        audio_tracks = []
        subtitle_tracks = []

        if metadata:
            for stream in metadata.get("streams", []):
                codec_name = stream.get("codec_name", "unknown")
                tags = stream.get("tags", {})
                lang = tags.get("language", "und").lower()
                title = tags.get("title")

                if stream.get("codec_type") == "video":
                    video_codec = codec_name
                    width = stream.get("width")
                    height = stream.get("height")
                    if width and height:
                        resolution = f"{width}x{height}"
                elif stream.get("codec_type") == "audio":
                    channels = stream.get("channels")
                    is_def = bool(stream.get("disposition", {}).get("default", 0))
                    is_frc = bool(stream.get("disposition", {}).get("forced", 0))
                    audio_tracks.append(
                        AudioTrackModel(
                            codec_name=codec_name,
                            language=lang,
                            channels=channels,
                            title=title,
                            is_default=is_def,
                            is_forced=is_frc,
                        )
                    )
                elif stream.get("codec_type") == "subtitle":
                    is_def = bool(stream.get("disposition", {}).get("default", 0))
                    is_frc = bool(stream.get("disposition", {}).get("forced", 0))
                    subtitle_tracks.append(
                        SubtitleTrackModel(
                            codec_name=codec_name,
                            language=lang,
                            title=title,
                            is_default=is_def,
                            is_forced=is_frc,
                            is_external=False,
                        )
                    )

        category = "TV Show" if self.is_tv_show(file_path.name) else "Movie"

        return MediaItemModel(
            path=str(file_path.absolute()),
            filename=file_path.name,
            category=category,
            file_size_bytes=file_size_bytes,
            file_size_human=self.format_size(file_size_bytes),
            container_format=container_format,
            duration_seconds=duration_seconds,
            resolution=resolution,
            video_codec=video_codec,
            bitrate_kbps=bitrate_kbps,
            audio_track_count=len(audio_tracks),
            subtitle_track_count=len(subtitle_tracks),
            audio_tracks=audio_tracks,
            subtitle_tracks=subtitle_tracks,
            analyzed_date=datetime.now().isoformat(),
            last_modified_date=datetime.now().isoformat(),
        )

    def analyze_path(self, base_dir: Path, recursive: bool = False, supported_extensions: list = None):
        if supported_extensions is None:
            supported_extensions = [".mkv", ".mp4", ".m4v", ".avi", ".mov"]

        base = Path(base_dir).expanduser()
        if not base.exists():
            return 0

        files_to_scan = []
        if recursive:
            for ext in supported_extensions:
                files_to_scan.extend(base.rglob(f"*{ext}"))
        else:
            for ext in supported_extensions:
                files_to_scan.extend(base.glob(f"*{ext}"))

        count = 0
        for file_path in files_to_scan:
            if file_path.is_file():
                model = self.extract_metadata(file_path)
                if model:
                    # Save to database
                    cat_id = self.db.get_or_create_category(model.category)
                    item_data = {
                        "category_id": cat_id,
                        "series_id": None,
                        "season_id": None,
                        "filename": model.filename,
                        "filepath": model.path,
                        "file_size_bytes": model.file_size_bytes,
                        "file_size_human": model.file_size_human,
                        "container_format": model.container_format,
                        "resolution": model.resolution,
                        "video_codec": model.video_codec,
                        "audio_track_count": model.audio_track_count,
                        "subtitle_track_count": model.subtitle_track_count,
                    }
                    self.db.insert_media_item(item_data)
                    count += 1
        return count
