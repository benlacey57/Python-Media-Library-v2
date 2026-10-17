from typing import List, Optional
from pydantic import BaseModel, Field


class AudioTrackModel(BaseModel):
    codec_name: str
    language: str
    channels: Optional[int] = None
    title: Optional[str] = None
    is_default: bool = False
    is_forced: bool = False


class SubtitleTrackModel(BaseModel):
    codec_name: str
    language: str
    title: Optional[str] = None
    is_default: bool = False
    is_forced: bool = False
    is_external: bool = False


class MediaItemModel(BaseModel):
    path: str
    filename: str
    category: str = "Movie"
    series_id: Optional[int] = None
    season_id: Optional[int] = None
    file_size_bytes: int = Field(..., ge=0)
    file_size_human: str = "0 MB"
    container_format: Optional[str] = None
    duration_seconds: float = 0.0
    resolution: str = "Unknown"
    video_codec: str = "unknown"
    bitrate_kbps: Optional[int] = None
    audio_track_count: int = 0
    subtitle_track_count: int = 0
    audio_tracks: List[AudioTrackModel] = []
    subtitle_tracks: List[SubtitleTrackModel] = []
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None
    external_subtitle_path: Optional[str] = None
    optimization_status: str = "Pending"
    naming_status: str = "Pending"


class SeriesModel(BaseModel):
    title: str = Field(..., min_length=1)
    sort_title: Optional[str] = None
    imdb_id: Optional[str] = None
    release_year: Optional[int] = Field(None, ge=1800, le=2100)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    genre: Optional[str] = None
    age_rating: Optional[str] = None
    total_seasons: int = 0
    total_episodes: int = 0
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    status: Optional[str] = None


class SeasonModel(BaseModel):
    series_id: int
    season_number: int
    name: Optional[str] = None
    episode_count: int = 0
    overview: Optional[str] = None


class MissingEpisodeModel(BaseModel):
    series_title: str
    season_number: int
    episode_number: int
    episode_title: Optional[str] = None
    air_date: Optional[str] = None
    overview: Optional[str] = None
    
