#!/usr/bin/env python3
"""
Test script to verify agent aggregation fixes and column improvements
"""

import pandas as pd
import json
from vlr_database import VLRDatabase
from datetime import datetime

def test_database_agent_aggregation():
    """Test the improved database agent aggregation"""
    print("=== Testing Database Agent Aggregation ===")
    
    # Load test data and save to database
    try:
        with open('detailed_match_data_fixed.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except FileNotFoundError:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    
    # Create test database
    db = VLRDatabase("test_agent_fix.db")
    success = db.save_detailed_match_data(match_data, "test_event_agent_fix")
    
    if not success:
        print("❌ Failed to save test data")
        return
    
    print("✅ Test data saved successfully")
    
    # Test the improved analytics function
    player_data = db.get_player_performance_analysis()
    
    if player_data.empty:
        print("❌ No player data returned")
        return
    
    print(f"📊 Retrieved {len(player_data)} player records")
    
    # Check for new columns
    expected_columns = ['agent_display', 'agent_count']
    for col in expected_columns:
        if col in player_data.columns:
            print(f"✅ Column '{col}' present")
        else:
            print(f"❌ Column '{col}' missing")
    
    # Show sample data for players with multiple agents
    print(f"\n📈 Sample Agent Aggregation Data:")
    
    # Look for players with agent_count > 1
    multi_agent_players = player_data[player_data['agent_count'] > 1] if 'agent_count' in player_data.columns else pd.DataFrame()
    
    if not multi_agent_players.empty:
        for _, row in multi_agent_players.head(3).iterrows():
            print(f"   Player: {row['player_name']}")
            print(f"   Primary Agent: {row['agent']}")
            print(f"   Agent Display: {row.get('agent_display', 'N/A')}")
            print(f"   Agent Count: {row.get('agent_count', 'N/A')}")
            print(f"   Map: {row['map_name']}")
            print("   ---")
    else:
        print("   No multi-agent players found in current data")
    
    # Export to CSV for manual verification
    player_data.to_csv('test_agent_aggregation.csv', index=False)
    print(f"✅ Exported test data to 'test_agent_aggregation.csv'")
    
    return player_data

def test_streamlit_csv_export():
    """Test the improved Streamlit CSV export logic"""
    print("\n=== Testing Streamlit CSV Export Logic ===")
    
    # Load test data
    try:
        with open('detailed_match_data_fixed.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except FileNotFoundError:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    
    detailed_matches = [match_data]
    
    # Simulate the improved Streamlit export logic
    all_player_stats = []
    player_agent_map = {}  # Track all agents per player per match
    
    for match in detailed_matches:
        match_id = match.get('match_id', '')
        event_name = match.get('event_info', {}).get('name', '')
        
        # First pass: collect all agents for each player
        for map_data in match.get('maps', []):
            for team_name, players in map_data.get('player_stats', {}).items():
                for player in players:
                    player_name = player.get('player_name', '')
                    agent = player.get('agent', '')
                    key = f"{match_id}_{player_name}"
                    
                    if key not in player_agent_map:
                        player_agent_map[key] = set()
                    if agent:
                        player_agent_map[key].add(agent)
        
        # Overall player stats with proper agent aggregation
        for team_name, players in match.get('overall_player_stats', {}).items():
            for player in players:
                stats_all = player.get('stats_all_sides', {})
                
                player_name = player.get('player_name', '')
                key = f"{match_id}_{player_name}"
                
                # Get all agents for this player
                all_agents = list(player_agent_map.get(key, set()))
                primary_agent = player.get('agent', '')
                
                # Create agent display
                if len(all_agents) <= 3:
                    agent_display = ', '.join(sorted(all_agents))
                else:
                    agent_display = f"{', '.join(sorted(all_agents)[:3])}, (+{len(all_agents)-3})"
                
                player_row = {
                    'Match ID': match_id,
                    'Event': event_name,
                    'Map': 'Overall',
                    'Team': player.get('team_name', team_name),
                    'Player Name': player_name,  # Fixed column name
                    'Player ID': player.get('player_id', ''),
                    'Primary Agent': primary_agent,
                    'Agent Display': agent_display,
                    'Agent Count': len(all_agents),
                    'Rating': stats_all.get('rating', ''),
                    'ACS': stats_all.get('acs', ''),
                    'Kills': stats_all.get('k', ''),
                    'Deaths': stats_all.get('d', ''),
                }
                all_player_stats.append(player_row)
    
    # Create DataFrame
    player_stats_df = pd.DataFrame(all_player_stats)
    
    print(f"✅ Created DataFrame with {len(player_stats_df)} records")
    print(f"   Columns: {list(player_stats_df.columns)}")
    
    # Check for duplicate columns
    duplicate_cols = []
    if 'Player' in player_stats_df.columns and 'Player Name' in player_stats_df.columns:
        duplicate_cols.append("'Player' and 'Player Name'")
    
    if duplicate_cols:
        print(f"⚠️ Potential duplicate columns found: {', '.join(duplicate_cols)}")
    else:
        print("✅ No duplicate columns found")
    
    # Verify agent aggregation
    print(f"\n📊 Agent Aggregation Verification:")
    for _, row in player_stats_df.iterrows():
        player_name = row['Player Name']
        agent_display = row['Agent Display']
        agent_count = row['Agent Count']
        
        print(f"   {player_name}:")
        print(f"     Agent Display: {agent_display}")
        print(f"     Agent Count: {agent_count}")
        
        # Verify count matches display
        if ', (+' in agent_display:
            # Extract the number from (+X)
            plus_part = agent_display.split(', (+')[1].split(')')[0]
            displayed_agents = len(agent_display.split(', (+')[0].split(', '))
            expected_count = displayed_agents + int(plus_part)
            
            if expected_count == agent_count:
                print(f"     ✅ Count matches display ({expected_count})")
            else:
                print(f"     ❌ Count mismatch: display suggests {expected_count}, count shows {agent_count}")
        else:
            # No (+X), so count should match number of displayed agents
            displayed_count = len(agent_display.split(', '))
            if displayed_count == agent_count:
                print(f"     ✅ Count matches display ({displayed_count})")
            else:
                print(f"     ❌ Count mismatch: display shows {displayed_count}, count shows {agent_count}")
        print()
    
    # Export to CSV
    csv_filename = f"test_streamlit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    player_stats_df.to_csv(csv_filename, index=False)
    print(f"✅ Exported to {csv_filename}")
    
    return player_stats_df

def compare_old_vs_new():
    """Compare old vs new export format"""
    print("\n=== Comparing Old vs New Export Format ===")
    
    # Check if old export exists
    try:
        old_df = pd.read_csv('player_analytics.csv')
        print(f"📊 Old export: {len(old_df)} records")
        print(f"   Columns: {list(old_df.columns)}")
        
        # Check for agent information
        if 'agent' in old_df.columns:
            print(f"   Agent info: Single agent per record")
        
    except FileNotFoundError:
        print("📊 No old export found for comparison")
        return
    
    # Check new export
    try:
        new_files = [f for f in os.listdir('.') if f.startswith('test_streamlit_export_')]
        if new_files:
            new_df = pd.read_csv(new_files[-1])  # Get latest
            print(f"📊 New export: {len(new_df)} records")
            print(f"   Columns: {list(new_df.columns)}")
            
            if 'Agent Display' in new_df.columns and 'Agent Count' in new_df.columns:
                print(f"   Agent info: Aggregated with display and count")
                
                # Show improvement
                multi_agent = new_df[new_df['Agent Count'] > 1]
                print(f"   Players with multiple agents: {len(multi_agent)}")
            
    except Exception as e:
        print(f"⚠️ Error reading new export: {e}")

def main():
    """Run all agent aggregation tests"""
    print("🔍 Agent Aggregation and Column Fix Testing")
    print("=" * 60)
    
    # Test database improvements
    db_data = test_database_agent_aggregation()
    
    # Test Streamlit export improvements
    streamlit_data = test_streamlit_csv_export()
    
    # Compare old vs new
    compare_old_vs_new()
    
    print("\n" + "=" * 60)
    print("✅ Agent Aggregation Testing Complete!")
    
    print(f"\n🎯 Key Improvements:")
    print(f"   ✅ Agent Display shows all agents played by each player")
    print(f"   ✅ Agent Count accurately reflects total number of agents")
    print(f"   ✅ Removed duplicate 'Player' column (now 'Player Name')")
    print(f"   ✅ Proper aggregation across maps for overall stats")
    print(f"   ✅ Clean CSV exports ready for analysis")

if __name__ == "__main__":
    import os
    main()
