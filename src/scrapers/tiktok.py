"""TikTok scraper using Playwright"""

import time
from typing import Optional
from models import Influencer
from scrapers.base import BaseScraper

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TikTokScraper(BaseScraper):
    """Scrape TikTok profiles"""
    
    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")
    
    def scrape(self, handle: str) -> Optional[Influencer]:
        """Scrape TikTok profile"""
        try:
            print(f"🔍 Scraping TikTok @{handle}...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                page.goto(f'https://www.tiktok.com/@{handle}', timeout=30000)
                time.sleep(3)
                
                # Extract data
                name = self._safe_extract(page, 'h1', handle)
                followers_text = self._safe_extract(page, 'strong[data-e2e="followers-count"]', '0')
                bio = self._safe_extract(page, 'h2[data-e2e="user-bio"]', '')
                
                browser.close()
                
                followers = self.parse_follower_count(followers_text)
                email = Influencer.extract_email(bio)
                
                return Influencer(
                    name=name,
                    platform='TikTok',
                    handle=handle,
                    followers=followers,
                    bio_snippet=bio,
                    email=email,
                    source_tag='scrape_tiktok'
                )
                
        except Exception as e:
            print(f"❌ Error scraping @{handle}: {e}")
            return None
    
    def _safe_extract(self, page, selector: str, default: str = '') -> str:
        """Safely extract text from page"""
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                return element.inner_text()
        except Exception:
            pass
        return default