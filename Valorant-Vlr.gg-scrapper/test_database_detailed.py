#!/usr/bin/env python3
"""
Test script to verify the updated VLR database functionality with detailed match data
"""

import json
import pandas as pd
from vlr_database import VLRDatabase
from datetime import datetime

def load_test_detailed_match():
    """Load test detailed match data"""
    try:
        with open('detailed_match_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: detailed_match_data.json not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def test_database_initialization():
    """Test database initialization with new tables"""
    print("=== Testing Database Initialization ===")
    
    db = VLRDatabase("test_detailed_vlr.db")
    
    # Check if all tables exist
    import sqlite3
    with sqlite3.connect("test_detailed_vlr.db") as conn:
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'events', 'matches', 'detailed_matches', 'map_details', 
            'player_stats', 'detailed_player_stats', 'agent_usage'
        ]
        
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
    
    print("Database initialization test complete.\n")
    return db

def test_save_detailed_match(db, match_data):
    """Test saving detailed match data"""
    print("=== Testing Detailed Match Data Saving ===")
    
    if not match_data:
        print("❌ No test data available")
        return False
    
    # Save the detailed match data
    success = db.save_detailed_match_data(match_data, "test_event_001")
    
    if success:
        print("✅ Detailed match data saved successfully")
        
        # Verify the data was saved
        match_id = match_data.get('match_id')
        saved_data = db.get_detailed_match_data(match_id)
        
        if saved_data:
            print(f"✅ Match data retrieved: {saved_data['match_info']['match_id']}")
            print(f"   - Event: {saved_data['match_info']['event_name']}")
            print(f"   - Teams: {saved_data['match_info']['team1_name']} vs {saved_data['match_info']['team2_name']}")
            print(f"   - Maps: {len(saved_data['maps'])} maps")
            print(f"   - Player records: {len(saved_data['player_stats'])} records")
        else:
            print("❌ Failed to retrieve saved match data")
            return False
    else:
        print("❌ Failed to save detailed match data")
        return False
    
    print("Detailed match data saving test complete.\n")
    return True

def test_comprehensive_data_saving(db, match_data):
    """Test saving data through the comprehensive data function"""
    print("=== Testing Comprehensive Data Saving ===")
    
    if not match_data:
        print("❌ No test data available")
        return False
    
    # Create a comprehensive data structure
    comprehensive_data = {
        'event_info': {
            'title': 'Test Event',
            'dates': '2024-07-17',
            'location': 'Online',
            'prize_pool': '$100,000',
            'description': 'Test tournament',
            'url': 'https://www.vlr.gg/event/test/test-event',
            'scraped_at': datetime.now().isoformat()
        },
        'matches_data': {
            'matches': [
                {
                    'match_id': match_data.get('match_id'),
                    'team1': match_data.get('teams', {}).get('team1', {}).get('name'),
                    'team2': match_data.get('teams', {}).get('team2', {}).get('name'),
                    'score': f"{match_data.get('teams', {}).get('team1', {}).get('score_overall', 0)}-{match_data.get('teams', {}).get('team2', {}).get('score_overall', 0)}",
                    'status': 'Completed',
                    'match_url': match_data.get('match_url'),
                    'scraped_at': datetime.now().isoformat()
                }
            ]
        },
        'stats_data': {
            'player_stats': []  # We'll use detailed stats instead
        },
        'maps_agents_data': {
            'agents': []  # We'll extract from detailed data
        },
        'detailed_matches': [match_data]
    }
    
    # Save comprehensive data
    event_id = db.save_comprehensive_data(comprehensive_data)
    
    if event_id:
        print(f"✅ Comprehensive data saved with event_id: {event_id}")
        
        # Retrieve and verify
        event_data = db.get_event_data(event_id)
        
        print(f"   - Events: {len(event_data['event_info'])} records")
        print(f"   - Matches: {len(event_data['matches'])} records")
        print(f"   - Detailed matches: {len(event_data['detailed_matches'])} records")
        print(f"   - Map details: {len(event_data['map_details'])} records")
        print(f"   - Detailed player stats: {len(event_data['detailed_player_stats'])} records")
    else:
        print("❌ Failed to save comprehensive data")
        return False
    
    print("Comprehensive data saving test complete.\n")
    return True

def test_analytics_functions(db):
    """Test the new analytics functions"""
    print("=== Testing Analytics Functions ===")
    
    # Test player performance analysis
    player_analysis = db.get_player_performance_analysis()
    print(f"✅ Player performance analysis: {len(player_analysis)} records")
    
    if not player_analysis.empty:
        top_player = player_analysis.iloc[0]
        print(f"   - Top performer: {top_player['player_name']} (Rating: {top_player['rating_all']:.2f})")
    
    # Test agent performance stats
    agent_stats = db.get_agent_performance_stats()
    print(f"✅ Agent performance stats: {len(agent_stats)} agents")
    
    if not agent_stats.empty:
        top_agent = agent_stats.iloc[0]
        print(f"   - Top agent: {top_agent['agent']} (Avg Rating: {top_agent['avg_rating']:.2f})")
    
    # Test map performance stats
    map_stats = db.get_map_performance_stats()
    print(f"✅ Map performance stats: {len(map_stats)} maps")
    
    if not map_stats.empty:
        most_played_map = map_stats.iloc[0]
        print(f"   - Most played map: {most_played_map['map_name']} ({most_played_map['times_played']} times)")
    
    print("Analytics functions test complete.\n")
    return True

def test_database_stats(db):
    """Test database statistics"""
    print("=== Testing Database Statistics ===")
    
    stats = db.get_database_stats()
    
    print("Database Statistics:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    size = db.get_database_size()
    print(f"   - Database size: {size}")
    
    print("Database statistics test complete.\n")
    return True

def main():
    """Run all tests"""
    print("Starting VLR Database Detailed Match Data Tests...\n")
    
    # Load test data
    match_data = load_test_detailed_match()
    
    # Initialize database
    db = test_database_initialization()
    
    # Run tests
    success = True
    success &= test_save_detailed_match(db, match_data)
    success &= test_comprehensive_data_saving(db, match_data)
    success &= test_analytics_functions(db)
    success &= test_database_stats(db)
    
    if success:
        print("✅ All tests passed! The database is ready for detailed match data.")
    else:
        print("❌ Some tests failed. Check the database implementation.")
    
    return success

if __name__ == "__main__":
    main()
