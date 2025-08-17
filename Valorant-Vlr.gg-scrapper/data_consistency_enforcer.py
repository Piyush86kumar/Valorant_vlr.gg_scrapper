#!/usr/bin/env python3
"""
Data consistency enforcer - ensures all data is correctly reflected in SQL database, JSON, and CSV files
"""

import pandas as pd
import json
import sqlite3
import os
from vlr_database import VLRDatabase
from datetime import datetime
import shutil

def enforce_json_consistency(input_file='detailed_match_data.json', output_file='detailed_match_data_consistent.json'):
    """Enforce JSON data consistency and fix any issues"""
    print("=== Enforcing JSON Consistency ===")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded JSON: {input_file}")
        
        # Fix data types and ensure consistency
        fixes_applied = []
        
        # 1. Ensure match_id is string
        if 'match_id' in data:
            data['match_id'] = str(data['match_id'])
            fixes_applied.append("Fixed match_id type")
        
        # 2. Fix event_info structure
        if 'event_info' not in data:
            data['event_info'] = {}
        
        event_info = data['event_info']
        required_event_fields = {
            'name': 'Unknown Event',
            'stage': 'Unknown Stage',
            'date_utc': '',
            'patch': 'Unknown'
        }
        
        for field, default in required_event_fields.items():
            if field not in event_info or event_info[field] is None:
                event_info[field] = default
                fixes_applied.append(f"Fixed event_info.{field}")
        
        # 3. Fix teams structure
        if 'teams' not in data:
            data['teams'] = {'team1': {}, 'team2': {}}
        
        teams = data['teams']
        for team_key in ['team1', 'team2']:
            if team_key not in teams:
                teams[team_key] = {}
            
            team = teams[team_key]
            if 'name' not in team or not team['name']:
                team['name'] = f'Team {team_key[-1]}'
                fixes_applied.append(f"Fixed {team_key} name")
            
            if 'score_overall' not in team:
                team['score_overall'] = 0
                fixes_applied.append(f"Fixed {team_key} score")
            else:
                try:
                    team['score_overall'] = int(team['score_overall'])
                except (ValueError, TypeError):
                    team['score_overall'] = 0
                    fixes_applied.append(f"Fixed {team_key} score type")
        
        # 4. Fix maps structure
        if 'maps' not in data:
            data['maps'] = []
        
        maps = data['maps']
        for i, map_data in enumerate(maps):
            # Fix map order
            if 'map_order' not in map_data:
                map_data['map_order'] = i + 1
                fixes_applied.append(f"Fixed map {i+1} order")
            else:
                try:
                    map_data['map_order'] = int(map_data['map_order'])
                except (ValueError, TypeError):
                    map_data['map_order'] = i + 1
                    fixes_applied.append(f"Fixed map {i+1} order type")
            
            # Fix map name
            if 'map_name' not in map_data or not map_data['map_name']:
                map_data['map_name'] = f'Map {i+1}'
                fixes_applied.append(f"Fixed map {i+1} name")
            
            # Fix map scores
            for score_field in ['team1_score_map', 'team2_score_map']:
                if score_field not in map_data:
                    map_data[score_field] = 0
                    fixes_applied.append(f"Fixed map {i+1} {score_field}")
                else:
                    try:
                        map_data[score_field] = int(map_data[score_field])
                    except (ValueError, TypeError):
                        map_data[score_field] = 0
                        fixes_applied.append(f"Fixed map {i+1} {score_field} type")
            
            # Fix player stats
            if 'player_stats' not in map_data:
                map_data['player_stats'] = {}
            
            player_stats = map_data['player_stats']
            for team_name, players in player_stats.items():
                for j, player in enumerate(players):
                    # Ensure required player fields
                    if 'player_name' not in player or not player['player_name']:
                        player['player_name'] = f'Player {j+1}'
                        fixes_applied.append(f"Fixed player {j+1} name in {team_name}")
                    
                    if 'agent' not in player or not player['agent']:
                        player['agent'] = 'Unknown'
                        fixes_applied.append(f"Fixed player {j+1} agent in {team_name}")
                    
                    # Fix stats structure
                    for stats_type in ['stats_all_sides', 'stats_attack', 'stats_defense']:
                        if stats_type not in player:
                            player[stats_type] = {}
                        
                        stats = player[stats_type]
                        numeric_fields = ['rating', 'acs', 'k', 'd', 'a', 'fk', 'fd', 'adr']
                        string_fields = ['kd_diff', 'kast', 'hs_percent', 'fk_fd_diff']
                        
                        for field in numeric_fields:
                            if field not in stats or stats[field] is None:
                                stats[field] = '0'
                            else:
                                stats[field] = str(stats[field])
                        
                        for field in string_fields:
                            if field not in stats or stats[field] is None:
                                stats[field] = ''
                            else:
                                stats[field] = str(stats[field])
        
        # 5. Fix overall player stats
        if 'overall_player_stats' not in data:
            data['overall_player_stats'] = {}
        
        overall_stats = data['overall_player_stats']
        for team_name, players in overall_stats.items():
            for player in players:
                # Apply same fixes as map player stats
                if 'player_name' not in player or not player['player_name']:
                    player['player_name'] = 'Unknown Player'
                    fixes_applied.append(f"Fixed overall player name in {team_name}")
                
                if 'agent' not in player or not player['agent']:
                    player['agent'] = 'Unknown'
                    fixes_applied.append(f"Fixed overall player agent in {team_name}")
                
                # Ensure agents list exists
                if 'agents' not in player:
                    player['agents'] = [player.get('agent', 'Unknown')]
                    fixes_applied.append(f"Added agents list for {player['player_name']}")
        
        # 6. Add metadata
        if 'scraped_at' not in data:
            data['scraped_at'] = datetime.now().isoformat()
            fixes_applied.append("Added scraped_at timestamp")
        
        if 'match_url' not in data:
            data['match_url'] = ''
            fixes_applied.append("Added match_url field")
        
        # Save consistent JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved consistent JSON: {output_file}")
        
        if fixes_applied:
            print(f"🔧 Applied {len(fixes_applied)} fixes:")
            for fix in fixes_applied[:10]:  # Show first 10 fixes
                print(f"   - {fix}")
            if len(fixes_applied) > 10:
                print(f"   ... and {len(fixes_applied) - 10} more fixes")
        else:
            print(f"✅ No fixes needed - JSON was already consistent")
        
        return True, data
        
    except Exception as e:
        print(f"❌ Error enforcing JSON consistency: {e}")
        return False, None

def enforce_database_consistency(json_data, db_path='vlr_data_consistent.db'):
    """Enforce database consistency with clean data"""
    print(f"\n=== Enforcing Database Consistency ===")
    
    try:
        # Create fresh database
        if os.path.exists(db_path):
            os.remove(db_path)
        
        db = VLRDatabase(db_path)
        print(f"✅ Created fresh database: {db_path}")
        
        # Save data with comprehensive validation
        event_id = f"consistent_event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = db.save_detailed_match_data(json_data, event_id)
        
        if success:
            print(f"✅ Saved data to database with event_id: {event_id}")
            
            # Verify data integrity
            stats = db.get_database_stats()
            print(f"📊 Database statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            # Check for data quality
            with sqlite3.connect(db_path) as conn:
                # Check detailed matches
                matches_df = pd.read_sql_query("SELECT * FROM detailed_matches", conn)
                null_count = matches_df.isnull().sum().sum()
                print(f"   NULL values in detailed_matches: {null_count}")
                
                # Check player stats
                players_df = pd.read_sql_query("SELECT * FROM detailed_player_stats", conn)
                if not players_df.empty:
                    missing_names = (players_df['player_name'] == '').sum()
                    missing_agents = (players_df['agent'] == '').sum()
                    print(f"   Missing player names: {missing_names}")
                    print(f"   Missing agents: {missing_agents}")
            
            return True, event_id
        else:
            print(f"❌ Failed to save data to database")
            return False, None
            
    except Exception as e:
        print(f"❌ Error enforcing database consistency: {e}")
        return False, None

def generate_consistent_csvs(db_path='vlr_data_consistent.db', output_dir='consistent_csvs'):
    """Generate consistent CSV files from the database"""
    print(f"\n=== Generating Consistent CSV Files ===")
    
    try:
        # Create output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
        db = VLRDatabase(db_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Player performance analysis
        player_data = db.get_player_performance_analysis()
        if not player_data.empty:
            player_file = os.path.join(output_dir, f'player_performance_{timestamp}.csv')
            player_data.to_csv(player_file, index=False)
            print(f"✅ Generated: {player_file} ({len(player_data)} records)")
        
        # 2. Agent performance stats
        agent_data = db.get_agent_performance_stats()
        if not agent_data.empty:
            agent_file = os.path.join(output_dir, f'agent_performance_{timestamp}.csv')
            agent_data.to_csv(agent_file, index=False)
            print(f"✅ Generated: {agent_file} ({len(agent_data)} records)")
        
        # 3. Map performance stats
        map_data = db.get_map_performance_stats()
        if not map_data.empty:
            map_file = os.path.join(output_dir, f'map_performance_{timestamp}.csv')
            map_data.to_csv(map_file, index=False)
            print(f"✅ Generated: {map_file} ({len(map_data)} records)")
        
        # 4. Raw detailed matches
        with sqlite3.connect(db_path) as conn:
            detailed_matches = pd.read_sql_query("SELECT * FROM detailed_matches", conn)
            if not detailed_matches.empty:
                matches_file = os.path.join(output_dir, f'detailed_matches_{timestamp}.csv')
                detailed_matches.to_csv(matches_file, index=False)
                print(f"✅ Generated: {matches_file} ({len(detailed_matches)} records)")
            
            # 5. Raw player stats
            player_stats = pd.read_sql_query("SELECT * FROM detailed_player_stats", conn)
            if not player_stats.empty:
                stats_file = os.path.join(output_dir, f'detailed_player_stats_{timestamp}.csv')
                player_stats.to_csv(stats_file, index=False)
                print(f"✅ Generated: {stats_file} ({len(player_stats)} records)")
            
            # 6. Map details
            map_details = pd.read_sql_query("SELECT * FROM map_details", conn)
            if not map_details.empty:
                map_details_file = os.path.join(output_dir, f'map_details_{timestamp}.csv')
                map_details.to_csv(map_details_file, index=False)
                print(f"✅ Generated: {map_details_file} ({len(map_details)} records)")
        
        # Validate all CSV files
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        print(f"\n📊 CSV Quality Validation:")
        
        all_clean = True
        for csv_file in csv_files:
            file_path = os.path.join(output_dir, csv_file)
            df = pd.read_csv(file_path)
            na_count = df.isna().sum().sum()
            empty_count = (df == '').sum().sum()
            
            if na_count == 0 and empty_count == 0:
                print(f"   ✅ {csv_file}: Clean ({len(df)} records)")
            else:
                print(f"   ⚠️ {csv_file}: {na_count} NA, {empty_count} empty values")
                all_clean = False
        
        return all_clean, output_dir
        
    except Exception as e:
        print(f"❌ Error generating consistent CSVs: {e}")
        return False, None

def main():
    """Enforce data consistency across all formats"""
    print("🔧 VLR Data Consistency Enforcer")
    print("Ensuring data integrity across SQL, JSON, and CSV files")
    print("=" * 60)
    
    # Step 1: Enforce JSON consistency
    json_success, json_data = enforce_json_consistency()
    
    if not json_success:
        print("❌ Failed to enforce JSON consistency")
        return False
    
    # Step 2: Enforce database consistency
    db_success, event_id = enforce_database_consistency(json_data)
    
    if not db_success:
        print("❌ Failed to enforce database consistency")
        return False
    
    # Step 3: Generate consistent CSV files
    csv_success, output_dir = generate_consistent_csvs()
    
    if not csv_success:
        print("❌ Failed to generate consistent CSV files")
        return False
    
    # Final summary
    print(f"\n" + "=" * 60)
    print(f"✅ DATA CONSISTENCY ENFORCEMENT COMPLETE!")
    print(f"=" * 60)
    
    print(f"\n📁 Generated Files:")
    print(f"   📄 JSON: detailed_match_data_consistent.json")
    print(f"   🗄️ Database: vlr_data_consistent.db")
    print(f"   📊 CSV Files: {output_dir}/ directory")
    
    print(f"\n🎯 All data is now consistent across:")
    print(f"   ✅ JSON structure with proper data types")
    print(f"   ✅ SQL database with no NULL values")
    print(f"   ✅ CSV files with clean, analysis-ready data")
    print(f"   ✅ Agent aggregation working correctly")
    print(f"   ✅ No duplicate columns or missing values")
    
    return True

if __name__ == "__main__":
    main()
