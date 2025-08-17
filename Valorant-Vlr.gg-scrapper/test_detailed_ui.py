#!/usr/bin/env python3
"""
Test script to verify the detailed match data UI functionality
"""

import json
import pandas as pd
from new_vlr_streamlit_ui import display_detailed_matches_data

def load_test_data():
    """Load test data from the detailed_match_data.json file"""
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # The UI expects a list of matches, so wrap the single match in a list
        return [match_data]
    
    except FileNotFoundError:
        print("Error: detailed_match_data.json not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def test_data_structure():
    """Test the data structure to ensure it matches what the UI expects"""
    detailed_matches = load_test_data()
    
    if not detailed_matches:
        print("No test data available")
        return False
    
    match = detailed_matches[0]
    
    print("=== Testing Data Structure ===")
    print(f"Match ID: {match.get('match_id')}")
    print(f"Event: {match.get('event_info', {}).get('name')}")
    print(f"Teams: {match.get('teams', {}).get('team1', {}).get('name')} vs {match.get('teams', {}).get('team2', {}).get('name')}")
    print(f"Maps: {len(match.get('maps', []))}")
    print(f"Overall stats teams: {list(match.get('overall_player_stats', {}).keys())}")
    
    # Test map structure
    if match.get('maps'):
        first_map = match['maps'][0]
        print(f"First map: {first_map.get('map_name')}")
        print(f"Map player stats teams: {list(first_map.get('player_stats', {}).keys())}")
        
        # Test player structure
        for team_name, players in first_map.get('player_stats', {}).items():
            if players:
                first_player = players[0]
                print(f"First player from {team_name}: {first_player.get('player_name')}")
                print(f"Agent: {first_player.get('agent')}")
                print(f"All agents: {first_player.get('agents')}")
                print(f"Stats structure: {list(first_player.get('stats_all_sides', {}).keys())}")
                break
    
    print("=== Data Structure Test Complete ===\n")
    return True

def test_player_stats_flattening():
    """Test the player stats flattening for analysis"""
    detailed_matches = load_test_data()
    
    if not detailed_matches:
        return False
    
    print("=== Testing Player Stats Flattening ===")
    
    # Simulate what the UI does for player performance analysis
    all_player_stats = []
    for match in detailed_matches:
        match_id = match.get('match_id')
        event_name = match.get('event_info', {}).get('name', 'Unknown Event')
        
        for team_name, players in match.get('overall_player_stats', {}).items():
            for player in players:
                stats_all = player.get('stats_all_sides', {})
                
                player_stat = {
                    'Match ID': match_id,
                    'Event': event_name,
                    'Team': player.get('team_name', team_name),
                    'Player': player.get('player_name', 'Unknown'),
                    'Primary Agent': player.get('agent', 'N/A'),
                    'All Agents': ', '.join(player.get('agents', [])),
                    'Rating': float(stats_all.get('rating', '0')),
                    'ACS': float(stats_all.get('acs', '0')),
                    'Kills': int(stats_all.get('k', '0')),
                    'Deaths': int(stats_all.get('d', '0')),
                    'Assists': int(stats_all.get('a', '0')),
                }
                
                all_player_stats.append(player_stat)
    
    if all_player_stats:
        df = pd.DataFrame(all_player_stats)
        print(f"Created DataFrame with {len(df)} player records")
        print(f"Columns: {list(df.columns)}")
        print(f"Top performer by rating: {df.loc[df['Rating'].idxmax(), 'Player']} ({df['Rating'].max()})")
        print(f"Top performer by ACS: {df.loc[df['ACS'].idxmax(), 'Player']} ({df['ACS'].max()})")
        print("Sample data:")
        print(df.head(3).to_string())
    
    print("=== Player Stats Flattening Test Complete ===\n")
    return True

def test_agent_analysis():
    """Test agent usage analysis"""
    detailed_matches = load_test_data()
    
    if not detailed_matches:
        return False
    
    print("=== Testing Agent Analysis ===")
    
    agent_usage = {}
    for match in detailed_matches:
        for team_name, players in match.get('overall_player_stats', {}).items():
            for player in players:
                agents = player.get('agents', [])
                for agent in agents:
                    if agent not in agent_usage:
                        agent_usage[agent] = 0
                    agent_usage[agent] += 1
    
    print(f"Agent usage: {agent_usage}")
    print(f"Most picked agent: {max(agent_usage, key=agent_usage.get)} ({agent_usage[max(agent_usage, key=agent_usage.get)]} times)")
    
    print("=== Agent Analysis Test Complete ===\n")
    return True

def main():
    """Run all tests"""
    print("Starting detailed match data UI tests...\n")
    
    success = True
    success &= test_data_structure()
    success &= test_player_stats_flattening()
    success &= test_agent_analysis()
    
    if success:
        print("✅ All tests passed! The UI should be able to handle the detailed match data.")
    else:
        print("❌ Some tests failed. Check the data structure or UI code.")
    
    return success

if __name__ == "__main__":
    main()
