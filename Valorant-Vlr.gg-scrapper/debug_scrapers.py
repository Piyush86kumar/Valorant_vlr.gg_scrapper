#!/usr/bin/env python3
"""
Debug script to test performance and economy scrapers
"""

import requests
from bs4 import BeautifulSoup
from detailed_match_performance_scrapper_v2 import DetailedMatchPerformanceScraper
from detailed_match_economy_scrapper import DetailedMatchEconomyScraper

def debug_html_structure(url, tab):
    """Debug the HTML structure of a VLR match page"""
    print(f"\n🔍 Debugging HTML structure for {tab} tab")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Construct URL with game=all and tab
    if '?' in url:
        full_url = f"{url}&game=all&tab={tab}"
    else:
        full_url = f"{url}?game=all&tab={tab}"
    
    print(f"📡 Fetching: {full_url}")
    
    try:
        response = session.get(full_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for common table structures
        print(f"\n📊 Looking for tables and data structures...")
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            headers = table.find_all('th')
            if headers:
                header_texts = [th.get_text(strip=True) for th in headers]
                print(f"  Headers: {header_texts}")
            
            rows = table.find_all('tr')
            print(f"  Rows: {len(rows)}")
            
            # Show first few data rows
            for j, row in enumerate(rows[:3]):
                cells = row.find_all(['td', 'th'])
                if cells and j > 0:  # Skip header row
                    cell_texts = [cell.get_text(strip=True)[:20] for cell in cells[:8]]  # First 8 cells, truncated
                    print(f"    Row {j}: {cell_texts}")
        
        # Look for specific div containers
        print(f"\n🎮 Looking for game containers...")
        game_containers = soup.find_all('div', class_='vm-stats-game')
        print(f"Found {len(game_containers)} vm-stats-game containers")
        
        # Look for other common structures
        wf_tables = soup.find_all('table', class_='wf-table-inset')
        print(f"Found {len(wf_tables)} wf-table-inset tables")
        
        return soup
        
    except Exception as e:
        print(f"❌ Error fetching HTML: {e}")
        return None

def test_scrapers():
    """Test both scrapers with debug output"""
    test_url = "https://www.vlr.gg/378822/drx-vs-sentinels-valorant-champions-2024-ubqf"
    
    print("🧪 Testing VLR Scrapers")
    print("=" * 50)
    
    # Debug HTML structure first
    perf_soup = debug_html_structure(test_url, "performance")
    econ_soup = debug_html_structure(test_url, "economy")
    
    print("\n" + "="*50)
    print("🎯 Testing Performance Scraper")
    print("="*50)
    
    perf_scraper = DetailedMatchPerformanceScraper()
    perf_result = perf_scraper.get_match_performance_data(test_url)
    
    if perf_result:
        print("✅ Performance scraper returned data")
        print(f"Keys: {list(perf_result.keys())}")
        perf_data = perf_result.get('performance_data', {})
        print(f"Performance data keys: {list(perf_data.keys())}")
        
        if perf_data:
            first_map_key = list(perf_data.keys())[0]
            first_map = perf_data[first_map_key]
            print(f"First map ({first_map_key}): {list(first_map.keys())}")
            
            if 'team1_players' in first_map:
                team1_count = len(first_map['team1_players'])
                team2_count = len(first_map['team2_players'])
                print(f"Team1 players: {team1_count}, Team2 players: {team2_count}")
                
                if team1_count > 0:
                    sample_player = first_map['team1_players'][0]
                    print(f"Sample player data keys: {list(sample_player.keys())}")
    else:
        print("❌ Performance scraper returned None")
    
    print("\n" + "="*50)
    print("💰 Testing Economy Scraper")
    print("="*50)
    
    econ_scraper = DetailedMatchEconomyScraper()
    econ_result = econ_scraper.get_match_economy_data(test_url)
    
    if econ_result:
        print("✅ Economy scraper returned data")
        print(f"Keys: {list(econ_result.keys())}")
        econ_data = econ_result.get('economy_data', {})
        print(f"Economy data keys: {list(econ_data.keys())}")
        
        if econ_data:
            first_map_key = list(econ_data.keys())[0]
            first_map = econ_data[first_map_key]
            print(f"First map ({first_map_key}): {list(first_map.keys())}")
            
            if 'economy_stats' in first_map:
                stats = first_map['economy_stats']
                team1_count = len(stats.get('team1_players', []))
                team2_count = len(stats.get('team2_players', []))
                print(f"Team1 players: {team1_count}, Team2 players: {team2_count}")
                
                if team1_count > 0:
                    sample_player = stats['team1_players'][0]
                    print(f"Sample player data keys: {list(sample_player.keys())}")
    else:
        print("❌ Economy scraper returned None")

if __name__ == "__main__":
    test_scrapers()
