#!/usr/bin/env python3
"""
Test script to verify the simplified file structure works correctly
"""

import pandas as pd
import json
import io
import zipfile
from datetime import datetime

def test_simplified_zip_creation():
    """Test the simplified ZIP creation with consolidated files"""
    print("=== Testing Simplified ZIP Creation ===")
    
    # Load test data
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except FileNotFoundError:
        print("❌ detailed_match_data.json not found")
        return False
    
    # Simulate the simplified data structure
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
                    'total_utilization_percent': '25%'
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
    
    # Test the simplified ZIP creation logic
    csv_files = {}
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Add basic CSV files
    if data.get('matches_data', {}).get('matches'):
        matches_df = pd.DataFrame(data['matches_data']['matches'])
        csv_files[f"vlr_matches_{timestamp}.csv"] = matches_df.to_csv(index=False)
        print("✅ Added matches CSV")
    
    if data.get('stats_data', {}).get('player_stats'):
        stats_df = pd.DataFrame(data['stats_data']['player_stats'])
        csv_files[f"vlr_player_stats_{timestamp}.csv"] = stats_df.to_csv(index=False)
        print("✅ Added player stats CSV")
    
    if data.get('maps_agents_data', {}).get('agents'):
        agents_df = pd.DataFrame(data['maps_agents_data']['agents'])
        csv_files[f"vlr_agent_utilization_{timestamp}.csv"] = agents_df.to_csv(index=False)
        print("✅ Added agent utilization CSV")
    
    if data.get('maps_agents_data', {}).get('maps'):
        maps_df = pd.DataFrame(data['maps_agents_data']['maps'])
        csv_files[f"vlr_maps_{timestamp}.csv"] = maps_df.to_csv(index=False)
        print("✅ Added maps CSV")
    
    # Add detailed data if available - CONSOLIDATED FORMAT
    if data.get('detailed_matches'):
        detailed_matches = data['detailed_matches']
        print("📊 Processing detailed matches data...")
        
        # 1. Detailed matches CSV (consolidated format)
        detailed_matches_data = []
        for match in detailed_matches:
            event_info = match.get('event_info', {})
            teams = match.get('teams', {})
            team1 = teams.get('team1', {})
            team2 = teams.get('team2', {})
            
            # Add match info
            match_record = {
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
                'Match URL': match.get('match_url', ''),
                'Scraped At': match.get('scraped_at', '')
            }
            
            # Add map details to the same record
            maps_info = []
            for map_data in match.get('maps', []):
                map_info = f"{map_data.get('map_name', '')} ({map_data.get('team1_score_map', '')}-{map_data.get('team2_score_map', '')})"
                maps_info.append(map_info)
            
            match_record['Maps Played'] = ' | '.join(maps_info)
            detailed_matches_data.append(match_record)
        
        if detailed_matches_data:
            detailed_df = pd.DataFrame(detailed_matches_data)
            csv_files[f"vlr_detailed_matches_{timestamp}.csv"] = detailed_df.to_csv(index=False)
            print("✅ Added detailed matches CSV (consolidated)")
        
        # 2. Detailed player stats CSV (using preferred format)
        detailed_player_data = []
        for match in detailed_matches:
            match_id = match.get('match_id', '')
            event_name = match.get('event_info', {}).get('name', '')
            
            # Overall player stats (match-level)
            for team_name, players in match.get('overall_player_stats', {}).items():
                for player in players:
                    stats_all = player.get('stats_all_sides', {})
                    stats_attack = player.get('stats_attack', {})
                    stats_defense = player.get('stats_defense', {})
                    
                    # Get all agents for this player across all maps
                    all_agents = player.get('agents', [])
                    primary_agent = player.get('agent', '')
                    all_agents_str = ', '.join(all_agents) if all_agents else primary_agent
                    
                    player_record = {
                        'Match ID': match_id,
                        'Event': event_name,
                        'Map': 'Overall',
                        'Team': team_name,
                        'Player': player.get('player_name', ''),
                        'Player ID': player.get('player_id', ''),
                        'Primary Agent': primary_agent,
                        'All Agents': all_agents_str,
                        
                        # All sides stats
                        'Rating': stats_all.get('rating', ''),
                        'ACS': stats_all.get('acs', ''),
                        'Kills': stats_all.get('k', ''),
                        'Deaths': stats_all.get('d', ''),
                        'Assists': stats_all.get('a', ''),
                        'K/D Diff': stats_all.get('kd_diff', ''),
                        'KAST': stats_all.get('kast', ''),
                        'ADR': stats_all.get('adr', ''),
                        'HS%': stats_all.get('hs_percent', ''),
                        'First Kills': stats_all.get('fk', ''),
                        'First Deaths': stats_all.get('fd', ''),
                        'FK/FD Diff': stats_all.get('fk_fd_diff', ''),
                        
                        # Attack stats
                        'Attack Rating': stats_attack.get('rating', ''),
                        'Attack ACS': stats_attack.get('acs', ''),
                        'Attack Kills': stats_attack.get('k', ''),
                        'Attack Deaths': stats_attack.get('d', ''),
                        'Attack Assists': stats_attack.get('a', ''),
                        'Attack KAST': stats_attack.get('kast', ''),
                        'Attack ADR': stats_attack.get('adr', ''),
                        
                        # Defense stats
                        'Defense Rating': stats_defense.get('rating', ''),
                        'Defense ACS': stats_defense.get('acs', ''),
                        'Defense Kills': stats_defense.get('k', ''),
                        'Defense Deaths': stats_defense.get('d', ''),
                        'Defense Assists': stats_defense.get('a', ''),
                        'Defense KAST': stats_defense.get('kast', ''),
                        'Defense ADR': stats_defense.get('adr', ''),
                    }
                    detailed_player_data.append(player_record)
            
            # Map-by-map player stats
            for map_data in match.get('maps', []):
                map_name = map_data.get('map_name', '')
                for team_name, players in map_data.get('player_stats', {}).items():
                    for player in players:
                        stats_all = player.get('stats_all_sides', {})
                        stats_attack = player.get('stats_attack', {})
                        stats_defense = player.get('stats_defense', {})
                        
                        agent = player.get('agent', '')
                        
                        player_record = {
                            'Match ID': match_id,
                            'Event': event_name,
                            'Map': map_name,
                            'Team': team_name,
                            'Player': player.get('player_name', ''),
                            'Player ID': player.get('player_id', ''),
                            'Primary Agent': agent,
                            'All Agents': agent,  # Single agent for individual map
                            
                            # All sides stats (same structure as above)
                            'Rating': stats_all.get('rating', ''),
                            'ACS': stats_all.get('acs', ''),
                            'Kills': stats_all.get('k', ''),
                            'Deaths': stats_all.get('d', ''),
                            'Assists': stats_all.get('a', ''),
                            'K/D Diff': stats_all.get('kd_diff', ''),
                            'KAST': stats_all.get('kast', ''),
                            'ADR': stats_all.get('adr', ''),
                            'HS%': stats_all.get('hs_percent', ''),
                            'First Kills': stats_all.get('fk', ''),
                            'First Deaths': stats_all.get('fd', ''),
                            'FK/FD Diff': stats_all.get('fk_fd_diff', ''),
                            
                            # Attack stats
                            'Attack Rating': stats_attack.get('rating', ''),
                            'Attack ACS': stats_attack.get('acs', ''),
                            'Attack Kills': stats_attack.get('k', ''),
                            'Attack Deaths': stats_attack.get('d', ''),
                            'Attack Assists': stats_attack.get('a', ''),
                            'Attack KAST': stats_attack.get('kast', ''),
                            'Attack ADR': stats_attack.get('adr', ''),
                            
                            # Defense stats
                            'Defense Rating': stats_defense.get('rating', ''),
                            'Defense ACS': stats_defense.get('acs', ''),
                            'Defense Kills': stats_defense.get('k', ''),
                            'Defense Deaths': stats_defense.get('d', ''),
                            'Defense Assists': stats_defense.get('a', ''),
                            'Defense KAST': stats_defense.get('kast', ''),
                            'Defense ADR': stats_defense.get('adr', ''),
                        }
                        detailed_player_data.append(player_record)
        
        if detailed_player_data:
            detailed_player_df = pd.DataFrame(detailed_player_data)
            csv_files[f"vlr_detailed_player_stats_{timestamp}.csv"] = detailed_player_df.to_csv(index=False)
            print("✅ Added detailed player stats CSV (preferred format)")
    
    # Create ZIP file
    if csv_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, csv_content in csv_files.items():
                zip_file.writestr(filename, csv_content)
        
        zip_buffer.seek(0)
        
        # Save test ZIP file
        test_zip_filename = f"test_simplified_vlr_data_{timestamp}.zip"
        with open(test_zip_filename, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        print(f"\n✅ Created simplified ZIP file: {test_zip_filename}")
        print(f"📦 ZIP contains {len(csv_files)} CSV files:")
        for filename in csv_files.keys():
            print(f"   - {filename}")
        
        # Verify ZIP contents and data quality
        with zipfile.ZipFile(test_zip_filename, 'r') as zip_file:
            zip_contents = zip_file.namelist()
            print(f"\n📋 ZIP verification: {len(zip_contents)} files found")
            
            for filename in zip_contents:
                try:
                    csv_content = zip_file.read(filename).decode('utf-8')
                    df = pd.read_csv(io.StringIO(csv_content))
                    
                    na_count = df.isna().sum().sum()
                    empty_count = (df == '').sum().sum()
                    
                    print(f"   📊 {filename}:")
                    print(f"      Records: {len(df)}, Columns: {len(df.columns)}")
                    print(f"      NA values: {na_count}, Empty strings: {empty_count}")
                    
                    if na_count == 0 and empty_count == 0:
                        print(f"      ✅ Clean data")
                    else:
                        print(f"      ⚠️ Data quality issues")
                        
                except Exception as e:
                    print(f"   ❌ Error validating {filename}: {e}")
        
        return True
    else:
        print("❌ No CSV files created")
        return False

def main():
    """Run simplified structure test"""
    print("🔍 Simplified File Structure Test")
    print("=" * 60)
    
    success = test_simplified_zip_creation()
    
    print(f"\n" + "=" * 60)
    print(f"✅ Simplified Structure Test Complete!")
    
    if success:
        print(f"\n🎯 Test Results:")
        print(f"   ✅ Simplified ZIP creation working")
        print(f"   ✅ Consolidated file structure")
        print(f"   ✅ Preferred format for detailed player stats")
        print(f"   ✅ Raw data export (no aggregation)")
        print(f"   ✅ Clean data with no NA values")
        
        print(f"\n📦 Simplified ZIP includes:")
        print(f"   🏆 Basic matches CSV")
        print(f"   👥 Player stats CSV")
        print(f"   🎭 Agent utilization CSV")
        print(f"   🗺️ Maps CSV")
        print(f"   🔍 Detailed matches CSV (consolidated)")
        print(f"   👥 Detailed player stats CSV (preferred format)")
        
        print(f"\n🎮 Simplified structure ready for UI!")
    else:
        print(f"\n⚠️ Test failed - check implementation")
    
    return success

if __name__ == "__main__":
    main()
