"""Data models and validation"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import re


@dataclass
class Influencer:
    """Influencer data model with validation"""
    name: str
    platform: str
    handle: str
    followers: int
    avg_engagement: float = 0.0
    primary_niche: str = ''
    content_style: str = ''
    bio_snippet: str = ''
    email: str = ''
    location: str = ''
    post_count: int = 0
    verified: bool = False
    last_post_date: str = ''
    source_tag: str = 'manual'
    date_added: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate and clean data"""
        self.name = self.name.strip()
        self.handle = self.handle.strip().lstrip('@')
        self.platform = self.platform.capitalize()
        self.bio_snippet = self.bio_snippet[:200]
        
        if not self.name:
            raise ValueError("Name is required")
        if not self.handle:
            raise ValueError("Handle is required")
        if self.followers < 0:
            raise ValueError("Followers must be positive")
        if not (0 <= self.avg_engagement <= 100):
            self.avg_engagement = max(0, min(100, self.avg_engagement))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV"""
        return asdict(self)
    
    @staticmethod
    def extract_email(text: str) -> str:
        """Extract email from text"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text or '')
        return match.group(0) if match else ''