"""
Dog Influencer Collector - Manual Entry Only
Simple version for manual data entry with CSV storage
"""

import csv
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


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


class InfluencerStorage:
    """Handle all CSV operations"""
    
    HEADERS = [
        'id', 'name', 'platform', 'handle', 'followers', 'avg_engagement',
        'primary_niche', 'content_style', 'bio_snippet', 'email', 'location',
        'post_count', 'date_added', 'source_tag', 'verified', 'last_post_date'
    ]
    
    def __init__(self, csv_path: str = 'dog_influencers.csv'):
        self.csv_path = Path(csv_path)
        self._init_csv()
    
    def _init_csv(self):
        """Create CSV if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writeheader()
    
    def get_next_id(self) -> int:
        """Get next available ID"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 1
    
    def exists(self, handle: str, platform: str) -> bool:
        """Check if influencer exists"""
        try:
            for influencer in self.get_all():
                if (influencer.handle.lower() == handle.lower() and 
                    influencer.platform == platform):
                    return True
        except FileNotFoundError:
            pass
        return False
    
    def add(self, influencer: Influencer) -> bool:
        """Add influencer to CSV"""
        try:
            # Check duplicate
            if self.exists(influencer.handle, influencer.platform):
                print(f"⚠️  @{influencer.handle} already exists")
                return False
            
            # Assign ID
            influencer.id = self.get_next_id()
            
            # Write
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writerow(influencer.to_dict())
            
            print(f"✅ Added: {influencer.name} (@{influencer.handle}) - "
                  f"{influencer.followers:,} followers [{influencer.source_tag}]")
            return True
            
        except Exception as e:
            print(f"❌ Error adding influencer: {e}")
            return False
    
    def get_all(self) -> List[Influencer]:
        """Get all influencers"""
        influencers = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    try:
                        row['followers'] = int(row.get('followers', 0))
                        row['avg_engagement'] = float(row.get('avg_engagement', 0))
                        row['post_count'] = int(row.get('post_count', 0))
                        row['verified'] = row.get('verified', '').lower() == 'true'
                        row['id'] = int(row.get('id', 0))
                        
                        influencers.append(Influencer(**row))
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  Skipping invalid row: {e}")
                        continue
        except FileNotFoundError:
            pass
        return influencers
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        influencers = self.get_all()
        
        if not influencers:
            return {'total': 0}
        
        stats = {
            'total': len(influencers),
            'sources': {},
            'platforms': {},
            'total_followers': sum(i.followers for i in influencers),
            'avg_engagement': sum(i.avg_engagement for i in influencers) / len(influencers),
            'verified_count': sum(1 for i in influencers if i.verified)
        }
        
        for inf in influencers:
            stats['sources'][inf.source_tag] = stats['sources'].get(inf.source_tag, 0) + 1
            stats['platforms'][inf.platform] = stats['platforms'].get(inf.platform, 0) + 1
        
        return stats


class DogInfluencerCollector:
    """Main application class"""
    
    # Constants
    NICHES = [
        'puppy_training', 'senior_dogs', 'rescue_advocate', 'dog_fashion',
        'active_dogs', 'dog_fitness', 'small_breeds', 'large_breeds',
        'dog_food_reviews', 'dog_toys', 'dog_health', 'dog_grooming'
    ]
    STYLES = ['Educational', 'Funny', 'Lifestyle', 'Product_Review', 'Storytelling']
    PLATFORMS = ['Instagram', 'TikTok', 'YouTube', 'Facebook']
    
    def __init__(self):
        self.storage = InfluencerStorage()
    
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
                
                # Platform selection (numbered picker)
                print("\nSelect platform:")
                for idx, p in enumerate(self.PLATFORMS, 1):
                    print(f"  {idx}. {p}")
                platform_input = input("Choice (number or name, default 1): ").strip()
                if platform_input.isdigit():
                    idx = int(platform_input)
                    platform = self.PLATFORMS[idx-1] if 1 <= idx <= len(self.PLATFORMS) else self.PLATFORMS[0]
                else:
                    platform = platform_input.capitalize() if platform_input else self.PLATFORMS[0]
                handle = input("Handle (no @): ").strip()
                followers = int(input("Followers: ").strip())
                avg_engagement = float(input("Avg Engagement %: ").strip() or 0)
                
                print(f"\nNiche ({', '.join(self.NICHES[:6])}...): ", end='')
                primary_niche = input().strip()
                
                content_style = input(f"Style ({'/'.join(self.STYLES)}): ").strip() or 'Funny'
                bio_snippet = input("Bio snippet: ").strip()
                email = input("Email: ").strip()
                location = input("Location: ").strip()
                post_count = int(input("Post count: ").strip() or 0)
                verified = input("Verified (y/n): ").strip().lower() == 'y'
                last_post_date = input("Last post date (YYYY-MM-DD): ").strip()
                
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
                    location=location,
                    post_count=post_count,
                    verified=verified,
                    last_post_date=last_post_date,
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
        print("\n🐕 DOG INFLUENCER COLLECTOR v3.0 (Manual Only)")
        print("="*50)
        print("Goal: 200 profiles | Manual Entry")
        print("="*50)
        
        while True:
            print("\nOptions:")
            print("1. Manual Entry")
            print("2. View Stats")
            print("3. Exit")
            
            choice = input("\nChoose: ").strip()
            
            try:
                if choice == '1':
                    self.manual_entry()
                elif choice == '2':
                    self.view_stats()
                elif choice == '3':
                    print("👋 Done! Check dog_influencers.csv")
                    break
                else:
                    print("❌ Invalid choice")
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == '__main__':
    app = DogInfluencerCollector()
    app.run()