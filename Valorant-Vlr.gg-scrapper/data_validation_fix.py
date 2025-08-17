#!/usr/bin/env python3
"""
Data validation and fixing script for VLR database
This script checks for and fixes data quality issues including NA values, missing values, and incorrect data types
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from vlr_database import VLRDatabase
from datetime import datetime

def check_database_data_quality(db_path="vlr_data.db"):
    """Check data quality in the database"""
    print("=== Database Data Quality Check ===")
    
    with sqlite3.connect(db_path) as conn:
        # Check detailed matches
        detailed_matches_df = pd.read_sql_query("SELECT * FROM detailed_matches", conn)
        print(f"\n📊 Detailed Matches Table:")
        print(f"   Total records: {len(detailed_matches_df)}")
        
        if not detailed_matches_df.empty:
            # Check for missing values
            missing_counts = detailed_matches_df.isnull().sum()
            if missing_counts.sum() > 0:
                print(f"   ⚠️ Missing values found:")
                for col, count in missing_counts[missing_counts > 0].items():
                    print(f"      {col}: {count} missing")
            else:
                print(f"   ✅ No missing values")
            
            # Check for empty strings
            empty_string_counts = (detailed_matches_df == '').sum()
            if empty_string_counts.sum() > 0:
                print(f"   ⚠️ Empty strings found:")
                for col, count in empty_string_counts[empty_string_counts > 0].items():
                    print(f"      {col}: {count} empty")
            else:
                print(f"   ✅ No empty strings")
        
        # Check detailed player stats
        player_stats_df = pd.read_sql_query("SELECT * FROM detailed_player_stats", conn)
        print(f"\n📊 Detailed Player Stats Table:")
        print(f"   Total records: {len(player_stats_df)}")
        
        if not player_stats_df.empty:
            # Check for missing values
            missing_counts = player_stats_df.isnull().sum()
            if missing_counts.sum() > 0:
                print(f"   ⚠️ Missing values found:")
                for col, count in missing_counts[missing_counts > 0].items():
                    print(f"      {col}: {count} missing")
            else:
                print(f"   ✅ No missing values")
            
            # Check for empty strings in text fields
            text_columns = ['player_name', 'team_name', 'agent', 'kd_diff_all', 'kast_all', 'hs_percent_all']
            for col in text_columns:
                if col in player_stats_df.columns:
                    empty_count = (player_stats_df[col] == '').sum()
                    if empty_count > 0:
                        print(f"   ⚠️ Empty strings in {col}: {empty_count}")
            
            # Check numeric ranges
            numeric_columns = ['rating_all', 'acs_all', 'kills_all', 'deaths_all']
            for col in numeric_columns:
                if col in player_stats_df.columns:
                    negative_count = (player_stats_df[col] < 0).sum()
                    if negative_count > 0:
                        print(f"   ⚠️ Negative values in {col}: {negative_count}")
        
        # Check map details
        map_details_df = pd.read_sql_query("SELECT * FROM map_details", conn)
        print(f"\n📊 Map Details Table:")
        print(f"   Total records: {len(map_details_df)}")
        
        if not map_details_df.empty:
            missing_counts = map_details_df.isnull().sum()
            if missing_counts.sum() > 0:
                print(f"   ⚠️ Missing values found:")
                for col, count in missing_counts[missing_counts > 0].items():
                    print(f"      {col}: {count} missing")
            else:
                print(f"   ✅ No missing values")

def test_csv_export_quality():
    """Test CSV export data quality"""
    print("\n=== CSV Export Quality Test ===")
    
    # Test with existing database
    db = VLRDatabase("test_detailed_vlr.db")
    
    # Get analytics data
    player_data = db.get_player_performance_analysis()
    agent_data = db.get_agent_performance_stats()
    map_data = db.get_map_performance_stats()
    
    datasets = [
        ("Player Analytics", player_data),
        ("Agent Analytics", agent_data),
        ("Map Analytics", map_data)
    ]
    
    for name, df in datasets:
        print(f"\n📊 {name}:")
        if df.empty:
            print(f"   ⚠️ No data available")
            continue
            
        print(f"   Total records: {len(df)}")
        
        # Check for NA values
        na_counts = df.isna().sum()
        if na_counts.sum() > 0:
            print(f"   ⚠️ NA values found:")
            for col, count in na_counts[na_counts > 0].items():
                print(f"      {col}: {count} NA values")
        else:
            print(f"   ✅ No NA values")
        
        # Check for empty strings
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            empty_count = (df[col] == '').sum()
            if empty_count > 0:
                print(f"   ⚠️ Empty strings in {col}: {empty_count}")

def fix_json_data_structure():
    """Fix JSON data structure to ensure proper format"""
    print("\n=== JSON Data Structure Fix ===")
    
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        print("✅ JSON file loaded successfully")
        
        # Validate required fields
        required_fields = ['match_id', 'event_info', 'teams', 'maps']
        missing_fields = []
        
        for field in required_fields:
            if field not in match_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
        
        # Check data types and fix if needed
        fixes_made = []
        
        # Ensure numeric fields are properly formatted
        if 'teams' in match_data:
            for team_key in ['team1', 'team2']:
                if team_key in match_data['teams']:
                    team = match_data['teams'][team_key]
                    if 'score_overall' in team:
                        try:
                            team['score_overall'] = int(team['score_overall'])
                            fixes_made.append(f"Fixed {team_key} score_overall type")
                        except (ValueError, TypeError):
                            team['score_overall'] = 0
                            fixes_made.append(f"Set {team_key} score_overall to 0 (invalid value)")
        
        # Fix map data
        if 'maps' in match_data:
            for i, map_data in enumerate(match_data['maps']):
                # Ensure map_order is integer
                if 'map_order' in map_data:
                    try:
                        map_data['map_order'] = int(map_data['map_order'])
                    except (ValueError, TypeError):
                        map_data['map_order'] = i + 1
                        fixes_made.append(f"Fixed map {i+1} order")
                
                # Fix player stats
                if 'player_stats' in map_data:
                    for team_name, players in map_data['player_stats'].items():
                        for j, player in enumerate(players):
                            # Fix numeric stats
                            for stat_category in ['stats_all_sides', 'stats_attack', 'stats_defense']:
                                if stat_category in player:
                                    stats = player[stat_category]
                                    for stat_name, stat_value in stats.items():
                                        if stat_name in ['rating', 'acs', 'adr']:
                                            try:
                                                stats[stat_name] = str(float(stat_value))
                                            except (ValueError, TypeError):
                                                stats[stat_name] = "0"
                                        elif stat_name in ['k', 'd', 'a', 'fk', 'fd']:
                                            try:
                                                stats[stat_name] = str(int(float(stat_value)))
                                            except (ValueError, TypeError):
                                                stats[stat_name] = "0"
        
        if fixes_made:
            print(f"🔧 Fixes applied:")
            for fix in fixes_made:
                print(f"   - {fix}")
            
            # Save fixed JSON
            with open('detailed_match_data_fixed.json', 'w', encoding='utf-8') as f:
                json.dump(match_data, f, indent=2, ensure_ascii=False)
            print("✅ Fixed JSON saved as 'detailed_match_data_fixed.json'")
        else:
            print("✅ No fixes needed")
            
    except FileNotFoundError:
        print("⚠️ detailed_match_data.json not found")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")

def create_clean_test_data():
    """Create clean test data and save to database"""
    print("\n=== Creating Clean Test Data ===")
    
    # Load and fix JSON data
    try:
        json_file = 'detailed_match_data_fixed.json' if os.path.exists('detailed_match_data_fixed.json') else 'detailed_match_data.json'
        with open(json_file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # Create new clean database
        db = VLRDatabase("clean_vlr_data.db")
        
        # Save the data
        success = db.save_detailed_match_data(match_data, "test_event_clean")
        
        if success:
            print("✅ Clean test data saved successfully")
            
            # Verify data quality
            stats = db.get_database_stats()
            print(f"📊 Clean Database Stats:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            # Export clean CSV
            player_data = db.get_player_performance_analysis()
            if not player_data.empty:
                player_data.to_csv('clean_player_analytics.csv', index=False)
                print("✅ Clean player analytics CSV exported")
                
                # Check for any remaining issues
                na_count = player_data.isna().sum().sum()
                empty_string_count = (player_data == '').sum().sum()
                print(f"   NA values: {na_count}")
                print(f"   Empty strings: {empty_string_count}")
        else:
            print("❌ Failed to save clean test data")
            
    except Exception as e:
        print(f"❌ Error creating clean test data: {e}")

def main():
    """Run all data validation and fixing procedures"""
    print("🔍 VLR Data Validation and Fixing Tool")
    print("=" * 50)
    
    # Check existing database quality
    check_database_data_quality()
    
    # Test CSV export quality
    test_csv_export_quality()
    
    # Fix JSON data structure
    fix_json_data_structure()
    
    # Create clean test data
    create_clean_test_data()
    
    print("\n" + "=" * 50)
    print("✅ Data validation and fixing complete!")
    print("\nRecommendations:")
    print("1. Use 'clean_vlr_data.db' for testing")
    print("2. Check 'clean_player_analytics.csv' for quality")
    print("3. Update Streamlit UI to use the improved data handling")
    print("4. Test CSV exports with the updated functions")

if __name__ == "__main__":
    import os
    main()
