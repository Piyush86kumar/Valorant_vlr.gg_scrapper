#!/usr/bin/env python3
"""
Test CSV generation with the updated coordinator
"""

from vlr_scraper_coordinator import VLRScraperCoordinator
import pandas as pd
from datetime import datetime

def test_csv_generation():
    """Test that all 8 CSV files are generated correctly"""
    print("🧪 Testing CSV Generation")
    print("=" * 50)
    
    # Test URL
    event_url = "https://www.vlr.gg/event/2097/valorant-champions-2024"
    
    # Initialize coordinator
    coordinator = VLRScraperCoordinator()
    
    print(f"📡 Testing with event URL: {event_url}")
    
    # Test comprehensive scraping with performance and economy
    print("\n🔍 Running comprehensive scraping...")
    result = coordinator.scrape_comprehensive(
        main_url=event_url,
        scrape_matches=True,
        scrape_stats=True,
        scrape_maps_agents=True,
        scrape_detailed_performance=True,
        scrape_detailed_economy=True
    )
    
    if not result:
        print("❌ Scraping failed!")
        return False
    
    print("✅ Scraping completed successfully!")
    
    # Test CSV generation logic (similar to Streamlit UI)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_files = {}
    
    # 1. Basic matches CSV
    matches = result.get('matches', [])
    if matches:
        matches_df = pd.DataFrame(matches)
        csv_files[f"vlr_matches_{timestamp}.csv"] = matches_df.to_csv(index=False)
        print(f"✅ Matches CSV: {len(matches)} records")
    else:
        print("❌ No matches data")
    
    # 2. Player stats CSV
    player_stats = result.get('player_stats', [])
    if player_stats:
        stats_df = pd.DataFrame(player_stats)
        csv_files[f"vlr_player_stats_{timestamp}.csv"] = stats_df.to_csv(index=False)
        print(f"✅ Player Stats CSV: {len(player_stats)} records")
    else:
        print("❌ No player stats data")
    
    # 3. Agent utilization CSV
    agent_utilization = result.get('agent_utilization', [])
    if agent_utilization:
        agent_df = pd.DataFrame(agent_utilization)
        csv_files[f"vlr_agent_utilization_{timestamp}.csv"] = agent_df.to_csv(index=False)
        print(f"✅ Agent Utilization CSV: {len(agent_utilization)} records")
    else:
        print("❌ No agent utilization data")
    
    # 4. Maps CSV
    maps = result.get('maps', [])
    if maps:
        maps_df = pd.DataFrame(maps)
        csv_files[f"vlr_maps_{timestamp}.csv"] = maps_df.to_csv(index=False)
        print(f"✅ Maps CSV: {len(maps)} records")
    else:
        print("❌ No maps data")
    
    # 5. Detailed matches CSV
    detailed_matches = result.get('detailed_matches', [])
    if detailed_matches:
        detailed_df = pd.DataFrame(detailed_matches)
        csv_files[f"vlr_detailed_matches_{timestamp}.csv"] = detailed_df.to_csv(index=False)
        print(f"✅ Detailed Matches CSV: {len(detailed_matches)} records")
    else:
        print("ℹ️ No detailed matches data (expected - not implemented in coordinator)")
    
    # 6. Performance data CSV
    performance_data = result.get('performance_data', {})
    if performance_data and performance_data.get('matches'):
        perf_records = []
        for match_data in performance_data['matches']:
            match_url = match_data.get('match_url', '')
            perf_data = match_data.get('performance_data', {})
            
            for map_key, map_data in perf_data.items():
                if isinstance(map_data, dict):
                    # Process team1 players
                    for player_data in map_data.get('team1_players', []):
                        record = {
                            'Match URL': match_url,
                            'Map': map_data.get('map_name', map_key),
                            'Team': 'Team 1',
                            'Player': player_data.get('player_name', ''),
                            '2K': player_data.get('multikills', {}).get('2k', 0),
                            '3K': player_data.get('multikills', {}).get('3k', 0),
                            '4K': player_data.get('multikills', {}).get('4k', 0),
                            '5K': player_data.get('multikills', {}).get('5k', 0),
                        }
                        perf_records.append(record)
                    
                    # Process team2 players
                    for player_data in map_data.get('team2_players', []):
                        record = {
                            'Match URL': match_url,
                            'Map': map_data.get('map_name', map_key),
                            'Team': 'Team 2',
                            'Player': player_data.get('player_name', ''),
                            '2K': player_data.get('multikills', {}).get('2k', 0),
                            '3K': player_data.get('multikills', {}).get('3k', 0),
                            '4K': player_data.get('multikills', {}).get('4k', 0),
                            '5K': player_data.get('multikills', {}).get('5k', 0),
                        }
                        perf_records.append(record)
        
        if perf_records:
            perf_df = pd.DataFrame(perf_records)
            csv_files[f"vlr_detailed_performance_{timestamp}.csv"] = perf_df.to_csv(index=False)
            print(f"✅ Performance CSV: {len(perf_records)} records")
        else:
            print("❌ No performance records generated")
    else:
        print("❌ No performance data")
    
    # 7. Economy data CSV
    economy_data = result.get('economy_data', {})
    if economy_data and economy_data.get('matches'):
        econ_records = []
        for match_data in economy_data['matches']:
            match_url = match_data.get('match_url', '')
            econ_data = match_data.get('economy_data', {})
            
            for map_key, map_data in econ_data.items():
                team_economy = map_data.get('team_economy', {})
                if team_economy:
                    # Process team1
                    team1_data = team_economy.get('team1', {})
                    if team1_data:
                        record = {
                            'Match URL': match_url,
                            'Map': map_data.get('map_name', map_key),
                            'Team': team1_data.get('team_name', 'Team 1'),
                            'Economy Type': 'Team Level',
                            'Pistol Won': team1_data.get('metrics', {}).get('Pistol Won', ''),
                            'Eco Won': team1_data.get('metrics', {}).get('Eco (won)', ''),
                        }
                        econ_records.append(record)
                    
                    # Process team2
                    team2_data = team_economy.get('team2', {})
                    if team2_data:
                        record = {
                            'Match URL': match_url,
                            'Map': map_data.get('map_name', map_key),
                            'Team': team2_data.get('team_name', 'Team 2'),
                            'Economy Type': 'Team Level',
                            'Pistol Won': team2_data.get('metrics', {}).get('Pistol Won', ''),
                            'Eco Won': team2_data.get('metrics', {}).get('Eco (won)', ''),
                        }
                        econ_records.append(record)
        
        if econ_records:
            econ_df = pd.DataFrame(econ_records)
            csv_files[f"vlr_detailed_economy_{timestamp}.csv"] = econ_df.to_csv(index=False)
            print(f"✅ Economy CSV: {len(econ_records)} records")
        else:
            print("❌ No economy records generated")
    else:
        print("❌ No economy data")
    
    # Summary
    print(f"\n📊 Summary: Generated {len(csv_files)} CSV files")
    for filename in csv_files.keys():
        print(f"   - {filename}")
    
    expected_files = [
        "vlr_matches_", "vlr_player_stats_", "vlr_agent_utilization_", 
        "vlr_maps_", "vlr_detailed_performance_", "vlr_detailed_economy_"
    ]
    
    generated_files = list(csv_files.keys())
    missing_files = []
    
    for expected in expected_files:
        if not any(expected in filename for filename in generated_files):
            missing_files.append(expected)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    else:
        print(f"\n✅ All expected CSV files generated successfully!")
        return True

if __name__ == "__main__":
    test_csv_generation()
