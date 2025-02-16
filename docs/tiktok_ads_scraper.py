#!/usr/bin/env python3
"""
TikTok Ad Library Scraper
-------------------------
A tool for collecting and analyzing ads from TikTok's Creative Center.
Supports multiple countries, keywords, and industries with data export capabilities.
"""

import os
import json
import time
import random
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Optional, Union
from pathlib import Path

class TikTokAdScraper:
    """Main class for scraping TikTok's Creative Center ad data."""
    
    BASE_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/list"
    
    def __init__(self, output_dir: str = "tiktok_ads_data"):
        """
        Initialize the TikTok Ad Scraper.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configure request session with necessary headers."""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://ads.tiktok.com",
            "Referer": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en"
        })
    
    def get_ads(self, 
                keywords: Optional[List[str]] = None,
                countries: Optional[List[str]] = None,
                industries: Optional[List[str]] = None,
                max_pages: int = 5,
                delay_range: tuple = (1, 3)) -> List[Dict]:
        """
        Fetch ads based on specified filters.
        
        Args:
            keywords: List of keywords to search for
            countries: List of country codes
            industries: List of industry names
            max_pages: Maximum number of pages to fetch
            delay_range: Range of seconds to delay between requests
            
        Returns:
            List of ad dictionaries
        """
        all_ads = []
        page = 1
        
        while page <= max_pages:
            params = {
                "page": page,
                "limit": 20,
                "period": 7,
                "sort_by": "trending",
            }
            
            if keywords:
                params["search_keys"] = ",".join(keywords)
            if countries:
                params["countries"] = ",".join(countries)
            if industries:
                params["industries"] = ",".join(industries)
            
            try:
                response = self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("data", {}).get("list"):
                    break
                    
                all_ads.extend(data["data"]["list"])
                print(f"Collected {len(all_ads)} ads...")
                
                page += 1
                time.sleep(random.uniform(*delay_range))
                
            except Exception as e:
                print(f"Error fetching page {page}: {str(e)}")
                break
        
        return all_ads
    
    def process_ads(self, ads: List[Dict]) -> pd.DataFrame:
        """
        Process raw ad data into a structured DataFrame.
        
        Args:
            ads: List of raw ad dictionaries
            
        Returns:
            Processed DataFrame
        """
        processed_data = []
        
        for ad in ads:
            processed_ad = {
                "title": ad.get("title"),
                "description": ad.get("description"),
                "industry": ad.get("industry"),
                "country": ad.get("country"),
                "video_url": ad.get("video_url"),
                "cover_image_url": ad.get("cover_image_url"),
                "likes": ad.get("likes"),
                "comments": ad.get("comments"),
                "shares": ad.get("shares"),
                "views": ad.get("views"),
                "posting_time": ad.get("posting_time"),
                "engagement_rate": ad.get("engagement_rate")
            }
            processed_data.append(processed_ad)
        
        return pd.DataFrame(processed_data)
    
    def save_data(self, df: pd.DataFrame, keywords: List[str]) -> str:
        """
        Save the DataFrame to Excel with formatting.
        
        Args:
            df: DataFrame to save
            keywords: Keywords used in the search
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"tiktok_ads_{'-'.join(keywords)}_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ad Data')
            
            # Format columns
            worksheet = writer.sheets['Ad Data']
            for idx, col in enumerate(df.columns, 1):
                worksheet.column_dimensions[chr(64 + idx)].width = 20
        
        return str(filename)

def main():
    """Main function to run the TikTok ad scraper."""
    # Initialize scraper
    scraper = TikTokAdScraper()
    
    # Get user inputs
    print("TikTok Ad Library Scraper")
    print("-" * 30)
    
    keywords = input("Enter keywords (comma-separated): ").split(",")
    keywords = [k.strip() for k in keywords if k.strip()]
    
    countries = input("Enter country codes (comma-separated) or press Enter for all: ").split(",")
    countries = [c.strip().upper() for c in countries if c.strip()] or None
    
    industries = input("Enter industries (comma-separated) or press Enter for all: ").split(",")
    industries = [i.strip() for i in industries if i.strip()] or None
    
    max_pages = int(input("Enter maximum number of pages to fetch (default 5): ") or "5")
    
    # Fetch and process ads
    print("\nFetching ads...")
    ads = scraper.get_ads(
        keywords=keywords,
        countries=countries,
        industries=industries,
        max_pages=max_pages
    )
    
    if not ads:
        print("No ads found!")
        return
    
    # Process and save data
    print("\nProcessing data...")
    df = scraper.process_ads(ads)
    
    filename = scraper.save_data(df, keywords)
    print(f"\nData saved to: {filename}")
    print(f"Total ads collected: {len(df)}")

if __name__ == "__main__":
    main()
