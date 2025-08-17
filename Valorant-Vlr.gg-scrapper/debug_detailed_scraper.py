#!/usr/bin/env python3
"""
Debug script to test detailed match scraper with a simple approach
"""

import requests
from bs4 import BeautifulSoup

def test_simple_scraping():
    """Test simple scraping without Selenium"""
    test_url = "https://www.vlr.gg/378662/gen-g-vs-sentinels-valorant-champions-2024-opening-b"
    
    print(f"Testing simple scraping with URL: {test_url}")
    print("=" * 80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we can find basic match info
        print("✅ Successfully fetched page content")
        
        # Look for match header
        match_header = soup.find('div', class_='match-header')
        if match_header:
            print("✅ Found match header")
            
            # Try to find team names
            team_elements = match_header.find_all('div', class_='wf-title-med')
            if team_elements:
                print(f"✅ Found {len(team_elements)} team elements")
                for i, team in enumerate(team_elements):
                    print(f"  Team {i+1}: {team.get_text(strip=True)}")
            else:
                print("❌ No team elements found")
        else:
            print("❌ No match header found")
            
        # Look for player stats tables
        stats_tables = soup.find_all('table', class_='wf-table-inset')
        print(f"✅ Found {len(stats_tables)} stats tables")
        
        # Look for map sections
        map_sections = soup.select('div.vm-stats-container > div.vm-stats-game')
        print(f"✅ Found {len(map_sections)} map sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_detailed_scraper():
    """Test the actual detailed match scraper"""
    print("\n" + "=" * 80)
    print("Testing actual MatchDetailsScraper")
    print("=" * 80)
    
    try:
        from match_details_scrapper import MatchDetailsScraper
        scraper = MatchDetailsScraper()
        
        test_url = "https://www.vlr.gg/378662/gen-g-vs-sentinels-valorant-champions-2024-opening-b"
        
        # Try without Selenium first (if possible)
        print("Attempting to scrape match details...")
        match_data = scraper.get_match_details(test_url)
        
        if not match_data:
            print("❌ No data returned from scraper")
            return False
            
        print("✅ Match data retrieved!")
        print(f"Match ID: {match_data.get('match_id', 'N/A')}")
        print(f"Event: {match_data.get('event_info', {}).get('name', 'N/A')}")
        
        teams = match_data.get('teams', {})
        team1 = teams.get('team1', {})
        team2 = teams.get('team2', {})
        print(f"Team 1: {team1.get('name', 'N/A')}")
        print(f"Team 2: {team2.get('name', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with detailed scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Debugging Detailed Match Scraper")
    print("=" * 80)
    
    # Test 1: Simple scraping
    simple_works = test_simple_scraping()
    
    # Test 2: Detailed scraper
    detailed_works = test_detailed_scraper()
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"Simple scraping: {'✅ Works' if simple_works else '❌ Failed'}")
    print(f"Detailed scraper: {'✅ Works' if detailed_works else '❌ Failed'}")
