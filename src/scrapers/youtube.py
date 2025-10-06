"""
YouTube scraper using multiple approaches:
1. YouTube Data API v3 (best, requires API key)
2. Web scraping with Playwright (fallback)
"""

import os
import time
from typing import Optional
from datetime import datetime
from models import Influencer
from scrapers.base import BaseScraper

# Try to import YouTube API
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class YouTubeScraper(BaseScraper):
    """
    Scrape YouTube channels
    Supports both API and web scraping methods
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube scraper
        
        Args:
            api_key: YouTube Data API v3 key (optional, but recommended)
                    Get one free at: https://console.cloud.google.com/
        """
        self.api_key = api_key or os.environ.get('YOUTUBE_API_KEY')
        self.youtube = None
        
        if self.api_key and YOUTUBE_API_AVAILABLE:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("✅ YouTube API initialized")
            except Exception as e:
                print(f"⚠️  YouTube API init failed: {e}")
        
        if not self.youtube and not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Neither YouTube API nor Playwright available.\n"
                "Install: pip install google-api-python-client\n"
                "Or: pip install playwright && playwright install"
            )
    
    def scrape(self, handle: str) -> Optional[Influencer]:
        """
        Scrape YouTube channel
        
        Args:
            handle: Can be @username, channel name, or channel ID
        
        Returns:
            Influencer object or None
        """
        print(f"🔍 Scraping YouTube: {handle}...")
        
        # Try API first (faster and more reliable)
        if self.youtube:
            result = self._scrape_with_api(handle)
            if result:
                return result
            print("⚠️  API scraping failed, trying web scraping...")
        
        # Fallback to web scraping
        if PLAYWRIGHT_AVAILABLE:
            return self._scrape_with_playwright(handle)
        
        print("❌ No scraping method available")
        return None
    
    def _scrape_with_api(self, handle: str) -> Optional[Influencer]:
        """Scrape using YouTube Data API v3"""
        try:
            # Handle different input formats
            channel_id = self._resolve_channel_id(handle)
            if not channel_id:
                return None
            
            # Get channel details
            request = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if not response.get('items'):
                print(f"❌ Channel not found: {handle}")
                return None
            
            channel = response['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']
            
            # Get recent videos for engagement calculation
            avg_engagement = self._calculate_engagement_api(channel_id)
            
            # Extract email from description
            email = Influencer.extract_email(snippet.get('description', ''))
            
            # Get last video date
            last_post_date = self._get_last_video_date_api(channel_id)
            
            return Influencer(
                name=snippet['title'],
                platform='YouTube',
                handle=snippet.get('customUrl', f"@{handle}").lstrip('@'),
                followers=int(stats.get('subscriberCount', 0)),
                avg_engagement=round(avg_engagement, 2),
                bio_snippet=snippet.get('description', '')[:200],
                email=email,
                location=snippet.get('country', ''),
                post_count=int(stats.get('videoCount', 0)),
                verified=False,  # Not available in API
                last_post_date=last_post_date,
                source_tag='scrape_youtube_api'
            )
            
        except HttpError as e:
            print(f"❌ YouTube API error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def _resolve_channel_id(self, handle: str) -> Optional[str]:
        """Convert @username or channel name to channel ID"""
        try:
            # If it looks like a channel ID (starts with UC)
            if handle.startswith('UC') and len(handle) == 24:
                return handle
            
            # Remove @ if present
            username = handle.lstrip('@')
            
            # Try search by username
            request = self.youtube.search().list(
                part='snippet',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                return response['items'][0]['snippet']['channelId']
            
            # Try forUsername endpoint
            request = self.youtube.channels().list(
                part='id',
                forUsername=username
            )
            response = request.execute()
            
            if response.get('items'):
                return response['items'][0]['id']
            
            print(f"❌ Could not resolve channel ID for: {handle}")
            return None
            
        except Exception as e:
            print(f"❌ Error resolving channel ID: {e}")
            return None
    
    def _calculate_engagement_api(self, channel_id: str) -> float:
        """Calculate average engagement rate from recent videos"""
        try:
            # Get recent videos
            request = self.youtube.search().list(
                part='id',
                channelId=channel_id,
                order='date',
                type='video',
                maxResults=10
            )
            response = request.execute()
            
            if not response.get('items'):
                return 0.0
            
            video_ids = [item['id']['videoId'] for item in response['items']]
            
            # Get video statistics
            request = self.youtube.videos().list(
                part='statistics',
                id=','.join(video_ids)
            )
            response = request.execute()
            
            if not response.get('items'):
                return 0.0
            
            # Calculate engagement (likes + comments) / views
            total_engagement = 0
            total_views = 0
            
            for video in response['items']:
                stats = video['statistics']
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                total_views += views
                total_engagement += likes + comments
            
            if total_views > 0:
                return (total_engagement / total_views) * 100
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _get_last_video_date_api(self, channel_id: str) -> str:
        """Get the date of the most recent video"""
        try:
            request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                order='date',
                type='video',
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                published_at = response['items'][0]['snippet']['publishedAt']
                # Convert from ISO format to YYYY-MM-DD
                return datetime.fromisoformat(published_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            
            return ''
        except Exception:
            return ''
    
    def _scrape_with_playwright(self, handle: str) -> Optional[Influencer]:
        """Scrape using Playwright (fallback method)"""
        try:
            print("🌐 Using web scraping (slower)...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Handle different URL formats
                if handle.startswith('@'):
                    url = f'https://www.youtube.com/{handle}/about'
                elif handle.startswith('UC'):
                    url = f'https://www.youtube.com/channel/{handle}/about'
                else:
                    url = f'https://www.youtube.com/@{handle}/about'
                
                page.goto(url, timeout=30000, wait_until='networkidle')
                time.sleep(3)  # Wait for dynamic content
                
                # Extract channel name
                name = self._safe_extract_pw(page, 'meta[property="og:title"]', 'content', handle)
                
                # Extract description
                description = self._safe_extract_pw(page, 'meta[property="og:description"]', 'content', '')
                
                # Extract subscriber count (appears in page text)
                page_text = page.content()
                subscribers = self._extract_subscriber_count(page_text)
                
                # Extract email from description
                email = Influencer.extract_email(description)
                
                browser.close()
                
                return Influencer(
                    name=name,
                    platform='YouTube',
                    handle=handle.lstrip('@'),
                    followers=subscribers,
                    avg_engagement=0.0,  # Can't get from web scraping
                    bio_snippet=description[:200],
                    email=email,
                    source_tag='scrape_youtube_web'
                )
                
        except Exception as e:
            print(f"❌ Error web scraping: {e}")
            return None
    
    def _safe_extract_pw(self, page, selector: str, attribute: str = None, default: str = '') -> str:
        """Safely extract text or attribute from page"""
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                if attribute:
                    return element.get_attribute(attribute) or default
                return element.inner_text()
        except Exception:
            pass
        return default
    
    def _extract_subscriber_count(self, page_text: str) -> int:
        """Extract subscriber count from page HTML"""
        import re
        
        # Pattern: "1.23M subscribers" or "123K subscribers"
        pattern = r'([\d.]+[KMB]?)\s+subscribers'
        match = re.search(pattern, page_text, re.IGNORECASE)
        
        if match:
            return self.parse_follower_count(match.group(1))
        
        return 0