# --- db_models.py ---

from dataclasses import dataclass
from typing import Optional

@dataclass
class Project:
    name: str
    priority: int
    due_date: str
    # IMPORTANT: Added for the image feature, even if not fully implemented yet
    thumbnail_path: Optional[str] = None 
    id: Optional[int] = None

@dataclass
class LogEntry:
    content: str
    project_id: int
    timestamp: str
    id: Optional[int] = None

@dataclass
class Attachment:
    file_path: str
    log_id: Optional[int] = None      # Can now be None if linked only to project/global
    project_id: Optional[int] = None  # NEW: Direct link to project
    is_global: bool = False           # NEW: Toggle for global availability
    is_thumbnail: bool = False
    id: Optional[int] = None