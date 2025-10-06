"""Command-line interface"""

import time
from pathlib import Path
from storage import InfluencerStorage
from models import Influencer
import os

# Constants
NICHES = [
    'puppy_training', 'senior_dogs', 'rescue_advocate', 'dog_fashion',
    'active_dogs', 'dog_fitness', 'small_breeds', 'large_breeds',
    'dog_food_reviews', 'dog_toys', 'dog_health', 'dog_grooming'
]
STYLES = ['Educational', 'Funny', 'Lifestyle', 'Product_Review', 'Storytelling']
PLATFORMS = ['Instagram', 'TikTok', 'YouTube', 'Facebook']


class CLI:
    """Command-line interface for the collector"""
    
    def __init__(self):
        self.storage = InfluencerStorage()
        self.instagram_scraper = None
        self.tiktok_scraper = None
    
    def _get_instagram_scraper(self):
        """Lazy load Instagram scraper"""
        if not self.instagram_scraper:
            try:
                from scrapers.instagram import InstagramScraper
                self.instagram_scraper = InstagramScraper()
            except ImportError as e:
                print(f"❌ {e}")
                return None
        return self.instagram_scraper
    
    def _get_tiktok_scraper(self):
        """Lazy load TikTok scraper"""
        if not self.tiktok_scraper:
            try:
                from scrapers.tiktok import TikTokScraper
                self.tiktok_scraper = TikTokScraper()
            except ImportError as e:
                print(f"❌ {e}")
                return None
        return self.tiktok_scraper
    
    def _get_youtube_scraper(self):
        '''Lazy load YouTube scraper'''
        if not self.youtube_scraper:
            try:
                from scrapers.youtube import YouTubeScraper
                
                # Try to get API key
                api_key = os.environ.get('YOUTUBE_API_KEY')
                if not api_key:
                    print("💡 Tip: Set YOUTUBE_API_KEY env var for faster scraping")
                    print("   Get one free at: https://console.cloud.google.com/")
                
                self.youtube_scraper = YouTubeScraper(api_key)
            except ImportError as e:
                print(f"❌ {e}")
                return None
        return self.youtube_scraper
    
    def scrape_youtube(self):
        '''Scrape single YouTube channel'''
        scraper = self._get_youtube_scraper()
        if not scraper:
            return
        
        print("\\nYou can provide:")
        print("  - @username (e.g., @MrBeast)")
        print("  - Channel ID (e.g., UCX6OQ3DkcsbYNE6H8uQQuVA)")
        print("  - Channel name")
        
        handle = input("\\nYouTube channel: ").strip()
        influencer = scraper.scrape(handle)
        
        if influencer:
            self.storage.add(influencer)
    
    def manual_entry(self):
        """Interactive manual entry"""
        print("\n--- MANUAL ENTRY MODE ---")
        print("(Leave 'Name' blank to exit)\n")
        
        while True:
            try:
                print("\n" + "="*50)
                name = input("Name: ").strip()
                if not name:
                    break
                
                platform = input(f"Platform ({'/'.join(PLATFORMS)}): ").strip() or 'Instagram'
                handle = input("Handle (no @): ").strip()
                followers = int(input("Followers: ").strip())
                avg_engagement = float(input("Avg Engagement %: ").strip() or 0)
                
                print(f"\nNiche ({', '.join(NICHES[:6])}...): ", end='')
                primary_niche = input().strip()
                
                content_style = input(f"Style ({'/'.join(STYLES)}): ").strip() or 'Funny'
                bio_snippet = input("Bio snippet: ").strip()
                email = input("Email: ").strip()
                
                influencer = Influencer(
                    name=name,
                    platform=platform,
                    handle=handle,
                    followers=followers,
                    avg_engagement=avg_engagement,
                    primary_niche=primary_niche,
                    content_style=content_style,
                    bio_snippet=bio_snippet,
                    email=email,
                    source_tag='manual'
                )
                
                self.storage.add(influencer)
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break
            except ValueError as e:
                print(f"❌ Invalid input: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def scrape_instagram(self):
        """Scrape single Instagram profile"""
        scraper = self._get_instagram_scraper()
        if not scraper:
            return
        
        handle = input("Instagram handle: ").strip()
        influencer = scraper.scrape(handle)
        
        if influencer:
            self.storage.add(influencer)
    
    def scrape_tiktok(self):
        """Scrape single TikTok profile"""
        scraper = self._get_tiktok_scraper()
        if not scraper:
            return
        
        handle = input("TikTok handle: ").strip()
        influencer = scraper.scrape(handle)
        
        if influencer:
            self.storage.add(influencer)
    
    def batch_import(self):
        """Import from file"""
        filepath = input("File path (one handle per line): ").strip()
        
        if not Path(filepath).exists():
            print(f"❌ File not found: {filepath}")
            return
        
        platform = input(f"Platform ({'/'.join(PLATFORMS)}): ").strip() or 'Instagram'
        
        # Read handles
        with open(filepath, 'r') as f:
            handles = [line.strip() for line in f if line.strip()]
        
        print(f"\n🚀 Batch scraping {len(handles)} {platform} profiles...")
        
        # Get scraper
        if platform == 'Instagram':
            scraper = self._get_instagram_scraper()
        elif platform == 'TikTok':
            scraper = self._get_tiktok_scraper()
        else:
            print(f"⚠️  Platform {platform} not supported for scraping")
            return
        
        if not scraper:
            return
        
        # Scrape
        success = 0
        for i, handle in enumerate(handles, 1):
            print(f"\n[{i}/{len(handles)}]")
            influencer = scraper.scrape(handle)
            
            if influencer and self.storage.add(influencer):
                success += 1
            
            time.sleep(2)  # Rate limiting
        
        print(f"\n✅ Batch complete: {success}/{len(handles)} added")
    
    def view_stats(self):
        """Display statistics"""
        stats = self.storage.get_stats()
        
        if stats['total'] == 0:
            print("\n📭 No influencers yet!")
            return
        
        print(f"\n{'='*50}")
        print(f"📊 COLLECTION STATS")
        print(f"{'='*50}")
        print(f"Total Profiles: {stats['total']} / 200 ({stats['total']/200*100:.1f}%)")
        print(f"Total Followers: {stats['total_followers']:,}")
        print(f"Avg Engagement: {stats['avg_engagement']:.2f}%")
        print(f"Verified: {stats['verified_count']}")
        
        print(f"\nSources:")
        for source, count in stats['sources'].items():
            print(f"  - {source}: {count}")
        
        print(f"\nPlatforms:")
        for platform, count in stats['platforms'].items():
            print(f"  - {platform}: {count}")
        
        print(f"{'='*50}\n")
    
    def run(self):
        """Main menu loop"""
        print("\n🐕 DOG INFLUENCER COLLECTOR v2.0 (Refactored)")
        print("="*50)
        print("Goal: 200 profiles | Modular & Maintainable")
        print("="*50)
        
        while True:
            print("\nOptions:")
            print("1. Manual Entry")
            print("2. Scrape Instagram Profile")
            print("3. Scrape TikTok Profile")
            print("4. Batch Import from File")
            print("5. View Stats")
            print("6. Exit")
            print("7. Scrape YouTube Channel")
            
            choice = input("\nChoose: ").strip()
            
            try:
                if choice == '1':
                    self.manual_entry()
                elif choice == '2':
                    self.scrape_instagram()
                elif choice == '3':
                    self.scrape_tiktok()
                elif choice == '4':
                    self.batch_import()
                elif choice == '5':
                    self.view_stats()
                elif choice == '6':
                    print("👋 Done! Check dog_influencers.csv")
                    break
                elif choice == '7':
                    self.scrape_youtube()
                else:
                    print("❌ Invalid choice")
            except Exception as e:
                print(f"❌ Error: {e}")