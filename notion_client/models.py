"""Simple Task model"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Task:
    """Simple task representation"""
    title: str
    status: str = "📋 À faire"
    sprint: Optional[str] = None
    mvp: Optional[str] = None
    priority: Optional[str] = None
    estimation: Optional[int] = None
    categories: List[str] = None
    notes: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []
