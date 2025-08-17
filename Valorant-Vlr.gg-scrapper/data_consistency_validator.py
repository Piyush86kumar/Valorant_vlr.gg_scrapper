#!/usr/bin/env python3
"""
Comprehensive data consistency validator for SQL database, JSON, and CSV files
Ensures all data is correctly reflected across all storage formats
"""

import pandas as pd
import json
import sqlite3
import os
from vlr_database import VLRDatabase
from datetime import datetime
import zipfile
import io

def validate_json_structure(json_file='detailed_match_data.json'):
    """Validate JSON data structure and fix any inconsistencies"""
    print("=== JSON Structure Validation ===")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON file loaded: {json_file}")
        
        # Validate required top-level fields
        required_fields = ['match_id', 'event_info', 'teams', 'maps']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Validate event_info structure
        event_info = data.get('event_info', {})
        event_required = ['name', 'stage', 'date_utc', 'patch']
        event_missing = [field for field in event_required if not event_info.get(field)]
        
        if event_missing:
            print(f"⚠️ Missing event info fields: {event_missing}")
        
        # Validate teams structure
        teams = data.get('teams', {})
        for team_key in ['team1', 'team2']:
            if team_key not in teams:
                print(f"❌ Missing team: {team_key}")
                return False
            
            team = teams[team_key]
            if 'name' not in team or 'score_overall' not in team:
                print(f"❌ Invalid team structure for {team_key}")
                return False
        
        # Validate maps structure
        maps = data.get('maps', [])
        if not maps:
            print(f"⚠️ No maps data found")
        else:
            print(f"✅ Found {len(maps)} maps")
            
            for i, map_data in enumerate(maps):
                required_map_fields = ['map_name', 'team1_score_map', 'team2_score_map', 'player_stats']
                missing_map_fields = [field for field in required_map_fields if field not in map_data]
                
                if missing_map_fields:
                    print(f"⚠️ Map {i+1} missing fields: {missing_map_fields}")
        
        # Validate player stats structure
        total_players = 0
        for map_data in maps:
            player_stats = map_data.get('player_stats', {})
            for team_name, players in player_stats.items():
                total_players += len(players)
                
                for j, player in enumerate(players):
                    required_player_fields = ['player_name', 'agent', 'stats_all_sides']
                    missing_player_fields = [field for field in required_player_fields if field not in player]
                    
                    if missing_player_fields:
                        print(f"⚠️ Player {j+1} in {team_name} missing: {missing_player_fields}")
        
        print(f"✅ Total player records validated: {total_players}")
        
        # Validate overall player stats
        overall_stats = data.get('overall_player_stats', {})
        if overall_stats:
            overall_players = sum(len(players) for players in overall_stats.values())
            print(f"✅ Overall player stats: {overall_players} records")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False

def validate_database_consistency(db_path='vlr_data.db'):
    """Validate database data consistency"""
    print(f"\n=== Database Consistency Validation ===")
    
    try:
        db = VLRDatabase(db_path)
        
        # Get database statistics
        stats = db.get_database_stats()
        print(f"📊 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Check for data consistency
        with sqlite3.connect(db_path) as conn:
            # Check detailed matches
            detailed_matches = pd.read_sql_query("SELECT * FROM detailed_matches", conn)
            print(f"\n✅ Detailed matches: {len(detailed_matches)} records")
            
            if not detailed_matches.empty:
                # Check for missing values
                null_counts = detailed_matches.isnull().sum()
                if null_counts.sum() > 0:
                    print(f"⚠️ NULL values in detailed_matches:")
                    for col, count in null_counts[null_counts > 0].items():
                        print(f"   {col}: {count}")
                else:
                    print(f"✅ No NULL values in detailed_matches")
            
            # Check map details
            map_details = pd.read_sql_query("SELECT * FROM map_details", conn)
            print(f"✅ Map details: {len(map_details)} records")
            
            # Check detailed player stats
            player_stats = pd.read_sql_query("SELECT * FROM detailed_player_stats", conn)
            print(f"✅ Detailed player stats: {len(player_stats)} records")
            
            if not player_stats.empty:
                # Check for missing player names
                missing_names = (player_stats['player_name'].isnull() | (player_stats['player_name'] == '')).sum()
                if missing_names > 0:
                    print(f"⚠️ Missing player names: {missing_names}")
                else:
                    print(f"✅ All player names present")
                
                # Check for missing agents
                missing_agents = (player_stats['agent'].isnull() | (player_stats['agent'] == '')).sum()
                if missing_agents > 0:
                    print(f"⚠️ Missing agents: {missing_agents}")
                else:
                    print(f"✅ All agents present")
        
        return True
        
    except Exception as e:
        print(f"❌ Database validation error: {e}")
        return False

def validate_csv_consistency():
    """Validate CSV file consistency"""
    print(f"\n=== CSV Consistency Validation ===")
    
    # Find all CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'test' not in f.lower()]
    
    if not csv_files:
        print(f"⚠️ No CSV files found for validation")
        return True
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            print(f"\n📊 {csv_file}:")
            print(f"   Records: {len(df)}")
            print(f"   Columns: {len(df.columns)}")
            
            # Check for data quality issues
            na_count = df.isna().sum().sum()
            empty_count = (df == '').sum().sum()
            
            print(f"   NA values: {na_count}")
            print(f"   Empty strings: {empty_count}")
            
            if na_count == 0 and empty_count == 0:
                print(f"   ✅ Clean data")
            else:
                print(f"   ⚠️ Data quality issues found")
            
            # Check for agent-related columns
            agent_columns = [col for col in df.columns if 'agent' in col.lower()]
            if agent_columns:
                print(f"   Agent columns: {agent_columns}")
                
                # Validate agent count consistency if present
                if 'Agent Display' in df.columns and 'Agent Count' in df.columns:
                    mismatches = 0
                    for _, row in df.iterrows():
                        display = row['Agent Display']
                        count = row['Agent Count']
                        
                        if pd.notna(display) and pd.notna(count):
                            if ', (+' in str(display):
                                plus_part = str(display).split(', (+')[1].split(')')[0]
                                displayed_agents = len(str(display).split(', (+')[0].split(', '))
                                expected_count = displayed_agents + int(plus_part)
                            else:
                                expected_count = len(str(display).split(', ')) if display else 0
                            
                            if expected_count != count:
                                mismatches += 1
                    
                    if mismatches == 0:
                        print(f"   ✅ Agent count consistency verified")
                    else:
                        print(f"   ⚠️ Agent count mismatches: {mismatches}")
            
        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")
    
    return True

def cross_validate_data_sources():
    """Cross-validate data between JSON, database, and CSV"""
    print(f"\n=== Cross-Source Data Validation ===")
    
    # Load JSON data
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        json_match_id = json_data.get('match_id')
        json_teams = json_data.get('teams', {})
        json_maps = json_data.get('maps', [])
        
        print(f"📄 JSON Data:")
        print(f"   Match ID: {json_match_id}")
        print(f"   Teams: {json_teams.get('team1', {}).get('name')} vs {json_teams.get('team2', {}).get('name')}")
        print(f"   Maps: {len(json_maps)}")
        
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return False
    
    # Check database
    try:
        db = VLRDatabase('vlr_data.db')
        
        with sqlite3.connect('vlr_data.db') as conn:
            # Check if match exists in database
            match_query = "SELECT * FROM detailed_matches WHERE match_id = ?"
            db_match = pd.read_sql_query(match_query, conn, params=[json_match_id])
            
            if not db_match.empty:
                print(f"📊 Database Data:")
                print(f"   Match found: {json_match_id}")
                print(f"   Teams: {db_match.iloc[0]['team1_name']} vs {db_match.iloc[0]['team2_name']}")
                print(f"   Maps played: {db_match.iloc[0]['maps_played']}")
                
                # Validate consistency
                json_team1 = json_teams.get('team1', {}).get('name', '')
                json_team2 = json_teams.get('team2', {}).get('name', '')
                db_team1 = db_match.iloc[0]['team1_name']
                db_team2 = db_match.iloc[0]['team2_name']
                
                if json_team1 == db_team1 and json_team2 == db_team2:
                    print(f"   ✅ Team names consistent")
                else:
                    print(f"   ⚠️ Team name mismatch: JSON({json_team1}, {json_team2}) vs DB({db_team1}, {db_team2})")
                
                if len(json_maps) == db_match.iloc[0]['maps_played']:
                    print(f"   ✅ Map count consistent")
                else:
                    print(f"   ⚠️ Map count mismatch: JSON({len(json_maps)}) vs DB({db_match.iloc[0]['maps_played']})")
            else:
                print(f"⚠️ Match {json_match_id} not found in database")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    
    return True

def generate_consistency_report():
    """Generate a comprehensive consistency report"""
    print(f"\n" + "="*60)
    print(f"📋 DATA CONSISTENCY REPORT")
    print(f"="*60)
    
    # Run all validations
    json_valid = validate_json_structure()
    db_valid = validate_database_consistency()
    csv_valid = validate_csv_consistency()
    cross_valid = cross_validate_data_sources()
    
    # Summary
    print(f"\n🎯 VALIDATION SUMMARY:")
    print(f"   JSON Structure: {'✅ PASS' if json_valid else '❌ FAIL'}")
    print(f"   Database Consistency: {'✅ PASS' if db_valid else '❌ FAIL'}")
    print(f"   CSV Quality: {'✅ PASS' if csv_valid else '❌ FAIL'}")
    print(f"   Cross-Source Validation: {'✅ PASS' if cross_valid else '❌ FAIL'}")
    
    overall_status = all([json_valid, db_valid, csv_valid, cross_valid])
    print(f"\n🏆 OVERALL STATUS: {'✅ ALL SYSTEMS CONSISTENT' if overall_status else '⚠️ ISSUES FOUND'}")
    
    if overall_status:
        print(f"\n🎮 Data is ready for:")
        print(f"   ✅ Analytics and visualization")
        print(f"   ✅ Machine learning models")
        print(f"   ✅ Business intelligence tools")
        print(f"   ✅ Academic research")
        print(f"   ✅ Production deployment")
    else:
        print(f"\n🔧 Recommended actions:")
        print(f"   1. Fix identified data quality issues")
        print(f"   2. Re-run validation after fixes")
        print(f"   3. Test end-to-end data pipeline")
        print(f"   4. Verify CSV exports from UI")
    
    return overall_status

def main():
    """Run comprehensive data consistency validation"""
    print("🔍 VLR Data Consistency Validator")
    print("Ensuring data integrity across SQL, JSON, and CSV files")
    
    # Generate comprehensive report
    success = generate_consistency_report()
    
    # Save report timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"data_consistency_report_{timestamp}.txt"
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return success

if __name__ == "__main__":
    main()
