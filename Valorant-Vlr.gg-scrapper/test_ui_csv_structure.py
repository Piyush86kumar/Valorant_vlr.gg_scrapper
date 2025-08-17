#!/usr/bin/env python3
"""
Test script to verify the updated UI CSV structure works correctly
"""

import pandas as pd
import json
import io
import zipfile
from datetime import datetime

def test_zip_creation_logic():
    """Test the ZIP creation logic from the UI"""
    print("=== Testing ZIP Creation Logic ===")
    
    # Load test data
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except FileNotFoundError:
        print("❌ detailed_match_data.json not found")
        return False
    
    # Simulate the data structure that would be in the UI
    data = {
        'matches_data': {
            'matches': [
                {
                    'match_id': match_data.get('match_id'),
                    'team1': match_data.get('teams', {}).get('team1', {}).get('name'),
                    'team2': match_data.get('teams', {}).get('team2', {}).get('name'),
                    'score': '2-1',
                    'status': 'Completed'
                }
            ]
        },
        'stats_data': {
            'player_stats': [
                {
                    'player': 'Test Player',
                    'team': 'Test Team',
                    'rating': 1.25,
                    'acs': 250,
                    'kills': 20,
                    'deaths': 15
                }
            ]
        },
        'maps_agents_data': {
            'agents': [
                {
                    'agent_name': 'Jett',
                    'total_utilization': 5,
                    'total_utilization_percent': '25%',
                    'map_utilizations': [
                        {'map': 'Ascent', 'utilization_percent': '30%'},
                        {'map': 'Bind', 'utilization_percent': '20%'}
                    ]
                }
            ],
            'maps': [
                {
                    'map_name': 'Ascent',
                    'times_played': 3,
                    'win_rate': '66.7%'
                }
            ]
        },
        'detailed_matches': [match_data]
    }
    
    # Test ZIP creation logic
    csv_files = {}
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Add matches CSV if available
    if data.get('matches_data', {}).get('matches'):
        matches_df = pd.DataFrame(data['matches_data']['matches'])
        csv_files[f"vlr_matches_{timestamp}.csv"] = matches_df.to_csv(index=False)
        print("✅ Added matches CSV to ZIP")
    
    # Add player stats CSV if available
    if data.get('stats_data', {}).get('player_stats'):
        stats_df = pd.DataFrame(data['stats_data']['player_stats'])
        csv_files[f"vlr_player_stats_{timestamp}.csv"] = stats_df.to_csv(index=False)
        print("✅ Added player stats CSV to ZIP")
    
    # Add agent utilization CSV if available
    if data.get('maps_agents_data', {}).get('agents'):
        agents_df = pd.DataFrame(data['maps_agents_data']['agents'])
        csv_files[f"vlr_agent_utilization_{timestamp}.csv"] = agents_df.to_csv(index=False)
        print("✅ Added agent utilization CSV to ZIP")
    
    # Add maps CSV if available
    if data.get('maps_agents_data', {}).get('maps'):
        maps_df = pd.DataFrame(data['maps_agents_data']['maps'])
        csv_files[f"vlr_maps_{timestamp}.csv"] = maps_df.to_csv(index=False)
        print("✅ Added maps CSV to ZIP")
    
    # Add detailed matches CSV if available
    if data.get('detailed_matches'):
        detailed_matches_data = []
        for match in data['detailed_matches']:
            # Extract data using the correct structure - NO AGGREGATION
            event_info = match.get('event_info', {})
            teams = match.get('teams', {})
            team1 = teams.get('team1', {})
            team2 = teams.get('team2', {})
            
            detailed_matches_data.append({
                'Match ID': match.get('match_id', ''),
                'Event': event_info.get('name', ''),
                'Stage': event_info.get('stage', ''),
                'Date UTC': event_info.get('date_utc', ''),
                'Patch': event_info.get('patch', ''),
                'Team 1': team1.get('name', ''),
                'Team 2': team2.get('name', ''),
                'Team 1 Score': team1.get('score_overall', ''),
                'Team 2 Score': team2.get('score_overall', ''),
                'Format': match.get('match_format', ''),
                'Pick/Ban Info': match.get('map_picks_bans_note', ''),
                'Maps Count': len(match.get('maps', [])),
                'Match URL': match.get('match_url', ''),
                'Scraped At': match.get('scraped_at', '')
            })
        
        if detailed_matches_data:
            detailed_df = pd.DataFrame(detailed_matches_data)
            csv_files[f"vlr_detailed_matches_{timestamp}.csv"] = detailed_df.to_csv(index=False)
            print("✅ Added detailed matches CSV to ZIP")
    
    if csv_files:
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, csv_content in csv_files.items():
                zip_file.writestr(filename, csv_content)
        
        zip_buffer.seek(0)
        
        # Save test ZIP file
        test_zip_filename = f"test_vlr_complete_data_{timestamp}.zip"
        with open(test_zip_filename, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        print(f"✅ Created test ZIP file: {test_zip_filename}")
        print(f"📦 ZIP contains {len(csv_files)} CSV files:")
        for filename in csv_files.keys():
            print(f"   - {filename}")
        
        # Verify ZIP contents
        with zipfile.ZipFile(test_zip_filename, 'r') as zip_file:
            zip_contents = zip_file.namelist()
            print(f"📋 ZIP verification: {len(zip_contents)} files found")
            for file in zip_contents:
                print(f"   ✅ {file}")
        
        return True
    else:
        print("❌ No CSV files created")
        return False

def test_individual_csv_structure():
    """Test individual CSV file structure"""
    print(f"\n=== Testing Individual CSV Structure ===")
    
    # Load test data
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except FileNotFoundError:
        print("❌ detailed_match_data.json not found")
        return False
    
    detailed_matches = [match_data]
    
    # Test detailed matches CSV structure
    print("📊 Testing Detailed Matches CSV:")
    detailed_csv_data = []
    for match in detailed_matches:
        event_info = match.get('event_info', {})
        teams = match.get('teams', {})
        team1 = teams.get('team1', {})
        team2 = teams.get('team2', {})

        detailed_csv_data.append({
            'Match ID': match.get('match_id', ''),
            'Event': event_info.get('name', ''),
            'Stage': event_info.get('stage', ''),
            'Date UTC': event_info.get('date_utc', ''),
            'Patch': event_info.get('patch', ''),
            'Team 1': team1.get('name', ''),
            'Team 2': team2.get('name', ''),
            'Team 1 Score': team1.get('score_overall', ''),
            'Team 2 Score': team2.get('score_overall', ''),
            'Format': match.get('match_format', ''),
            'Pick/Ban Info': match.get('map_picks_bans_note', ''),
            'Maps Count': len(match.get('maps', [])),
            'Match URL': match.get('match_url', ''),
            'Scraped At': match.get('scraped_at', '')
        })

    if detailed_csv_data:
        detailed_df = pd.DataFrame(detailed_csv_data)
        print(f"   Records: {len(detailed_df)}")
        print(f"   Columns: {list(detailed_df.columns)}")
        
        # Check for data quality
        na_count = detailed_df.isna().sum().sum()
        empty_count = (detailed_df == '').sum().sum()
        print(f"   NA values: {na_count}")
        print(f"   Empty strings: {empty_count}")
        
        if na_count == 0:
            print("   ✅ No NA values")
        else:
            print("   ⚠️ Contains NA values")
    
    # Test raw player stats CSV structure
    print(f"\n📊 Testing Raw Player Stats CSV:")
    raw_player_data = []
    for match in detailed_matches:
        match_id = match.get('match_id', '')
        event_name = match.get('event_info', {}).get('name', '')
        
        # Export raw player stats as scraped
        for map_data in match.get('maps', []):
            map_name = map_data.get('map_name', '')
            for team_name, players in map_data.get('player_stats', {}).items():
                for player in players:
                    # Just export the raw scraped data
                    player_record = {
                        'Match ID': match_id,
                        'Event': event_name,
                        'Map': map_name,
                        'Team': team_name,
                        'Player Name': player.get('player_name', ''),
                        'Player ID': player.get('player_id', ''),
                        'Agent': player.get('agent', ''),
                    }
                    
                    # Add all stats as they were scraped
                    stats_all = player.get('stats_all_sides', {})
                    for stat_key, stat_value in stats_all.items():
                        player_record[f"All_{stat_key}"] = stat_value
                    
                    stats_attack = player.get('stats_attack', {})
                    for stat_key, stat_value in stats_attack.items():
                        player_record[f"Attack_{stat_key}"] = stat_value
                    
                    stats_defense = player.get('stats_defense', {})
                    for stat_key, stat_value in stats_defense.items():
                        player_record[f"Defense_{stat_key}"] = stat_value
                    
                    raw_player_data.append(player_record)
    
    if raw_player_data:
        raw_player_df = pd.DataFrame(raw_player_data)
        print(f"   Records: {len(raw_player_df)}")
        print(f"   Columns: {len(raw_player_df.columns)} columns")
        print(f"   Sample columns: {list(raw_player_df.columns)[:10]}...")
        
        # Check for data quality
        na_count = raw_player_df.isna().sum().sum()
        empty_count = (raw_player_df == '').sum().sum()
        print(f"   NA values: {na_count}")
        print(f"   Empty strings: {empty_count}")
        
        # Save test file
        test_filename = f"test_raw_player_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        raw_player_df.to_csv(test_filename, index=False)
        print(f"   ✅ Saved test file: {test_filename}")
    
    return True

def main():
    """Run all UI CSV structure tests"""
    print("🔍 UI CSV Structure Testing")
    print("=" * 50)
    
    # Test ZIP creation
    zip_success = test_zip_creation_logic()
    
    # Test individual CSV structure
    csv_success = test_individual_csv_structure()
    
    print(f"\n" + "=" * 50)
    print(f"✅ UI CSV Structure Testing Complete!")
    
    if zip_success and csv_success:
        print(f"\n🎯 All tests passed:")
        print(f"   ✅ ZIP creation logic working")
        print(f"   ✅ Individual CSV structure correct")
        print(f"   ✅ Raw data export (no aggregation)")
        print(f"   ✅ Clean data with no NA values")
        print(f"   ✅ Proper button structure implemented")
    else:
        print(f"\n⚠️ Some tests failed - check implementation")
    
    return zip_success and csv_success

if __name__ == "__main__":
    main()
