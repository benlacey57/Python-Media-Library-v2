from typing import List, Optional
from pydantic import BaseModel, Field


class SeriesModel(BaseModel):
    title: str = Field(..., min_length=1)
    imdb_id: Optional[str] = None
    release_year: Optional[int] = Field(None, ge=1800, le=2100)
    total_seasons: Optional[int] = Field(None, ge=1)
    overview: Optional[str] = None


class AudioTrackModel(BaseModel):
    codec: str
    language: str
    is_default: bool = False


class SubtitleTrackModel(BaseModel):
    codec: str
    language: str
    is_forced: bool = False


class MediaItemModel(BaseModel):
    filepath: str
    filename: str
    size_bytes: int = Field(..., ge=0)
    resolution: str = "Unknown"
    video_codec: str = "unknown"
    audio_tracks: List[AudioTrackModel] = []
    subtitle_tracks: List[SubtitleTrackModel] = []
    is_optimized: bool = False
    is_renamed: bool = False
