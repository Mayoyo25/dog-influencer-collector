"""Instagram scraper using Instaloader"""

from typing import Optional
from models import Influencer
from scrapers.base import BaseScraper

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False


class InstagramScraper(BaseScraper):
    """Scrape Instagram profiles"""
    
    def __init__(self):
        if not INSTALOADER_AVAILABLE:
            raise ImportError("Instaloader not installed. Run: pip install instaloader")
        
        self.loader = instaloader.Instaloader()
        self.loader.context.quiet = True
    
    def scrape(self, handle: str) -> Optional[Influencer]:
        """Scrape Instagram profile"""
        try:
            print(f"🔍 Scraping Instagram @{handle}...")
            
            profile = instaloader.Profile.from_username(self.loader.context, handle)
            
            # Calculate engagement
            avg_engagement = self._calculate_engagement(profile)
            
            # Get last post date
            posts = list(profile.get_posts())
            last_post_date = posts[0].date.strftime('%Y-%m-%d') if posts else ''
            
            # Extract email
            email = Influencer.extract_email(profile.biography or '')
            
            return Influencer(
                name=profile.full_name or handle,
                platform='Instagram',
                handle=handle,
                followers=profile.followers,
                avg_engagement=round(avg_engagement, 2),
                bio_snippet=profile.biography or '',
                email=email,
                post_count=profile.mediacount,
                verified=profile.is_verified,
                last_post_date=last_post_date,
                source_tag='scrape_instagram'
            )
            
        except Exception as e:
            print(f"❌ Error scraping @{handle}: {e}")
            return None
    
    def _calculate_engagement(self, profile) -> float:
        """Calculate average engagement rate from recent posts"""
        try:
            posts = list(profile.get_posts())[:10]
            if not posts or profile.followers == 0:
                return 0.0
            
            total_engagement = sum((p.likes + p.comments) for p in posts)
            return (total_engagement / len(posts) / profile.followers) * 100
        except Exception:
            return 0.0