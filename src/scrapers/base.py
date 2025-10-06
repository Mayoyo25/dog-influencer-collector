"""Base scraper interface"""

from abc import ABC, abstractmethod
from typing import Optional
from models import Influencer


class BaseScraper(ABC):
    """Abstract base class for scrapers"""
    
    @abstractmethod
    def scrape(self, handle: str) -> Optional[Influencer]:
        """Scrape profile and return Influencer object"""
        pass
    
    @staticmethod
    def parse_follower_count(text: str) -> int:
        """Parse follower count from text like '1.2M' or '450K'"""
        text = str(text).upper().strip()
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    num = float(text.replace(suffix, '').replace(',', '').strip())
                    return int(num * multiplier)
                except ValueError:
                    pass
        
        try:
            return int(text.replace(',', ''))
        except ValueError:
            return 0