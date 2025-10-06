"""CSV storage management"""

import csv
from pathlib import Path
from typing import List, Dict
from models import Influencer


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
                    row['followers'] = int(row.get('followers', 0))
                    row['avg_engagement'] = float(row.get('avg_engagement', 0))
                    row['post_count'] = int(row.get('post_count', 0))
                    row['verified'] = row.get('verified', '').lower() == 'true'
                    row['id'] = int(row.get('id', 0))
                    
                    influencers.append(Influencer(**row))
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