from dataclasses import dataclass
from typing import Optional

@dataclass
class Project:
    name: str
    priority: int
    due_date: str
    id: Optional[int] = None  # Optional because new projects won't