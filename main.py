# main.py
"""
Dog Influencer Collector - Modular Architecture
Separated into: models, storage, scrapers, and CLI
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from cli import CLI

if __name__ == '__main__':
    cli = CLI()
    cli.run()