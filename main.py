import csv
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
import instaloader
from playwright.sync_api import sync_playwright
import time
import re

# CSV filename
CSV_FILE = 'dog_influencers.csv'

# Enhanced headers
HEADERS = [
    'id', 'name', 'platform', 'handle', 'followers', 'avg_engagement',
    'primary_niche', 'content_style', 'bio_snippet', 'email', 'location',
    'post_count', 'date_added', 'source_tag', 'verified', 'last_post_date'
]

# Reference data
NICHES = [
    'puppy_training', 'senior_dogs', 'rescue_advocate', 'dog_fashion',
    'active_dogs', 'dog_fitness', 'small_breeds', 'large_breeds',
    'dog_food_reviews', 'dog_toys', 'dog_health', 'dog_grooming',
    'working_dogs', 'service_dogs', 'dog_travel', 'dog_lifestyle',
    'funny_dogs', 'dog_photography', 'multi_dog_household'
]

STYLES = ['Educational', 'Funny', 'Lifestyle', 'Product_Review', 'Storytelling', 'Behind_The_Scenes']
PLATFORMS = ['Instagram', 'TikTok', 'YouTube', 'Facebook']


class DogInfluencerCollector:
    def __init__(self):
        self.csv_file = CSV_FILE
        self.init_csv()
        self.loader = None  # Lazy load instaloader
    
    def init_csv(self):
        """Create CSV with enhanced headers"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=HEADERS)
                writer.writeheader()
            print(f"✅ Created {self.csv_file}")
        else:
            print(f"📄 Using existing {self.csv_file}")
    
    def get_next_id(self) -> int:
        """Get next ID by counting rows"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 1
    
    def handle_exists(self, handle: str, platform: str) -> bool:
        """Check if handle already exists for platform"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['handle'].lower() == handle.lower() and row['platform'] == platform:
                        return True
        except FileNotFoundError:
            pass
        return False
    
    def extract_email_from_bio(self, bio: str) -> str:
        """Extract email from bio text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, bio)
        return match.group(0) if match else ''
    
    def add_influencer(self, data: Dict, source_tag: str = 'manual') -> bool:
        """Add influencer with source tagging"""
        
        # Validation
        if not data.get('name') or not data.get('handle') or not data.get('followers'):
            print("❌ Missing required: name, handle, followers")
            return False
        
        # Check duplicates
        if self.handle_exists(data['handle'], data.get('platform', 'Instagram')):
            print(f"⚠️  {data['handle']} already exists. Skipping.")
            return False
        
        # Prepare row
        row = {
            'id': self.get_next_id(),
            'name': data.get('name', ''),
            'platform': data.get('platform', 'Instagram'),
            'handle': data.get('handle', ''),
            'followers': data.get('followers', 0),
            'avg_engagement': data.get('avg_engagement', 0),
            'primary_niche': data.get('primary_niche', ''),
            'content_style': data.get('content_style', ''),
            'bio_snippet': data.get('bio_snippet', '')[:200],  # Limit bio
            'email': data.get('email', ''),
            'location': data.get('location', ''),
            'post_count': data.get('post_count', 0),
            'date_added': datetime.now().strftime('%Y-%m-%d'),
            'source_tag': source_tag,
            'verified': data.get('verified', False),
            'last_post_date': data.get('last_post_date', '')
        }
        
        # Append
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writerow(row)
        
        print(f"✅ Added: {row['name']} (@{row['handle']}) - {row['followers']:,} followers [{source_tag}]")
        return True
    
    # ============= INSTAGRAM SCRAPER (using Instaloader) =============
    def scrape_instagram_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape Instagram profile using Instaloader
        No login required for public profiles
        """
        try:
            if not self.loader:
                self.loader = instaloader.Instaloader()
                self.loader.context.quiet = True
            
            print(f"🔍 Scraping @{username} on Instagram...")
            
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Calculate engagement from recent posts
            posts = list(profile.get_posts())[:10]
            if posts:
                total_engagement = sum((p.likes + p.comments) for p in posts)
                avg_engagement = (total_engagement / len(posts) / profile.followers) * 100
            else:
                avg_engagement = 0
            
            # Extract email from bio
            email = self.extract_email_from_bio(profile.biography)
            
            data = {
                'name': profile.full_name or username,
                'platform': 'Instagram',
                'handle': username,
                'followers': profile.followers,
                'avg_engagement': round(avg_engagement, 2),
                'bio_snippet': profile.biography[:200] if profile.biography else '',
                'email': email,
                'location': '',  # Not easily accessible
                'post_count': profile.mediacount,
                'verified': profile.is_verified,
                'last_post_date': posts[0].date.strftime('%Y-%m-%d') if posts else ''
            }
            
            return data
            
        except Exception as e:
            print(f"❌ Error scraping {username}: {str(e)}")
            return None
    
    # ============= TIKTOK SCRAPER (using Playwright) =============
    def scrape_tiktok_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape TikTok profile using Playwright
        Note: TikTok is more restrictive, may need rotation
        """
        try:
            print(f"🔍 Scraping @{username} on TikTok...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f'https://www.tiktok.com/@{username}', wait_until='networkidle')
                
                time.sleep(3)  # Wait for dynamic content
                
                # Extract data from page
                name = page.locator('h1').first.inner_text()
                
                # Followers (format: "1.2M followers")
                followers_text = page.locator('strong[data-e2e="followers-count"]').first.inner_text()
                followers = self.parse_follower_count(followers_text)
                
                # Bio
                bio = page.locator('h2[data-e2e="user-bio"]').first.inner_text() if page.locator('h2[data-e2e="user-bio"]').count() > 0 else ''
                
                # Email from bio
                email = self.extract_email_from_bio(bio)
                
                browser.close()
                
                data = {
                    'name': name,
                    'platform': 'TikTok',
                    'handle': username,
                    'followers': followers,
                    'avg_engagement': 0,  # TikTok doesn't show likes easily
                    'bio_snippet': bio[:200],
                    'email': email,
                    'location': '',
                    'post_count': 0,  # Hard to get without API
                    'verified': False
                }
                
                return data
                
        except Exception as e:
            print(f"❌ Error scraping TikTok {username}: {str(e)}")
            return None
    
    def parse_follower_count(self, text: str) -> int:
        """Parse follower count from text like '1.2M' or '450K'"""
        text = text.upper().strip()
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                num = float(text.replace(suffix, '').strip())
                return int(num * multiplier)
        
        return int(text.replace(',', ''))
    
    # ============= BATCH OPERATIONS =============
    def scrape_from_list(self, handles: List[str], platform: str = 'Instagram'):
        """Scrape multiple profiles from a list"""
        print(f"\n🚀 Batch scraping {len(handles)} {platform} profiles...")
        
        success = 0
        failed = 0
        
        for i, handle in enumerate(handles, 1):
            print(f"\n[{i}/{len(handles)}]")
            
            if platform == 'Instagram':
                data = self.scrape_instagram_profile(handle)
            elif platform == 'TikTok':
                data = self.scrape_tiktok_profile(handle)
            else:
                print(f"⚠️  Platform {platform} not supported yet")
                continue
            
            if data:
                if self.add_influencer(data, source_tag=f'scrape_{platform.lower()}'):
                    success += 1
                else:
                    failed += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(2)
        
        print(f"\n✅ Batch complete: {success} added, {failed} failed/skipped")
    
    def import_from_file(self, filepath: str):
        """Import handles from text file (one per line)"""
        try:
            with open(filepath, 'r') as f:
                handles = [line.strip() for line in f if line.strip()]
            
            print(f"📋 Found {len(handles)} handles in {filepath}")
            platform = input("Platform (Instagram/TikTok): ").strip() or 'Instagram'
            
            self.scrape_from_list(handles, platform)
            
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
    
    # ============= MANUAL ENTRY =============
    def manual_entry(self):
        """Interactive manual entry"""
        print("\n--- MANUAL ENTRY MODE ---")
        print("(Press Ctrl+C to exit)\n")
        
        while True:
            try:
                print("\n" + "="*50)
                name = input("Name: ").strip()
                if not name:
                    break
                
                print(f"Platform ({', '.join(PLATFORMS)}): ", end='')
                platform = input().strip() or 'Instagram'
                
                handle = input("Handle (no @): ").strip()
                followers = int(input("Followers: ").strip())
                avg_engagement = float(input("Avg Engagement %: ").strip())
                
                print(f"\nNiche options: {', '.join(NICHES[:10])}...")
                primary_niche = input("Primary Niche: ").strip()
                
                print(f"Style ({', '.join(STYLES)}): ", end='')
                content_style = input().strip() or 'Funny'
                
                post_count = int(input("Post Count: ").strip())
                bio_snippet = input("Bio (first 200 chars): ").strip()
                email = input("Email: ").strip()
                location = input("Location: ").strip()
                
                data = {
                    'name': name, 'platform': platform, 'handle': handle,
                    'followers': followers, 'avg_engagement': avg_engagement,
                    'primary_niche': primary_niche, 'content_style': content_style,
                    'bio_snippet': bio_snippet, 'email': email,
                    'location': location, 'post_count': post_count
                }
                
                self.add_influencer(data, source_tag='manual')
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break
            except ValueError as e:
                print(f"❌ Invalid input: {e}")
    
    # ============= STATS & REPORTING =============
    def view_stats(self):
        """Enhanced stats with source breakdown"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            if not data:
                print("📭 No influencers yet!")
                return
            
            total = len(data)
            sources = {}
            platforms = {}
            
            for row in data:
                sources[row.get('source_tag', 'unknown')] = sources.get(row.get('source_tag', 'unknown'), 0) + 1
                platforms[row['platform']] = platforms.get(row['platform'], 0) + 1
            
            print(f"\n{'='*50}")
            print(f"📊 COLLECTION STATS")
            print(f"{'='*50}")
            print(f"Total Profiles: {total} / 200 ({total/200*100:.1f}%)")
            print(f"\nSources:")
            for source, count in sources.items():
                print(f"  - {source}: {count}")
            print(f"\nPlatforms:")
            for platform, count in platforms.items():
                print(f"  - {platform}: {count}")
            print(f"{'='*50}\n")
            
        except FileNotFoundError:
            print("📭 No data yet!")
    
    # ============= MAIN MENU =============
    def run(self):
        """Main interactive menu"""
        print("\n🐕 DOG INFLUENCER COLLECTOR v2.0")
        print("="*50)
        print("Goal: 200 profiles in Week 1")
        print("Tools: Manual, Instagram Scraper, TikTok Scraper")
        print("="*50)
        
        while True:
            print("\nOptions:")
            print("1. Manual Entry")
            print("2. Scrape Instagram Profile")
            print("3. Scrape TikTok Profile")
            print("4. Batch Import from File")
            print("5. View Stats")
            print("6. Exit")
            
            choice = input("\nChoose: ").strip()
            
            if choice == '1':
                self.manual_entry()
            elif choice == '2':
                handle = input("Instagram handle: ").strip()
                data = self.scrape_instagram_profile(handle)
                if data:
                    self.add_influencer(data, source_tag='scrape_instagram')
            elif choice == '3':
                handle = input("TikTok handle: ").strip()
                data = self.scrape_tiktok_profile(handle)
                if data:
                    self.add_influencer(data, source_tag='scrape_tiktok')
            elif choice == '4':
                filepath = input("File path (one handle per line): ").strip()
                self.import_from_file(filepath)
            elif choice == '5':
                self.view_stats()
            elif choice == '6':
                print("👋 Done! Check dog_influencers.csv")
                break
            else:
                print("Invalid choice")


if __name__ == '__main__':
    collector = DogInfluencerCollector()
    collector.run()