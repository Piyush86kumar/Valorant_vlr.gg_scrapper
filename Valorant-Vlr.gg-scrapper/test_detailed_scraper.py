#!/usr/bin/env python3
"""
Quick test script to verify the detailed match scraper is working correctly
"""

from match_details_scrapper import MatchDetailsScraper
import json

def test_detailed_scraper():
    """Test the detailed match scraper with a sample URL"""
    scraper = MatchDetailsScraper()
    
    # Test URL - the one you mentioned in your example
    test_url = "https://www.vlr.gg/378662/gen-g-vs-sentinels-valorant-champions-2024-opening-b"
    
    print(f"Testing detailed match scraper with URL: {test_url}")
    print("=" * 80)
    
    try:
        # Get match details
        match_data = scraper.get_match_details(test_url)
        
        if not match_data:
            print("❌ No data returned from scraper")
            return False
            
        # Check key fields
        print("✅ Match data retrieved successfully!")
        print("\n📋 Basic Match Info:")
        print(f"  Match ID: {match_data.get('match_id', 'N/A')}")
        print(f"  Event: {match_data.get('event_info', {}).get('name', 'N/A')}")
        print(f"  Date: {match_data.get('event_info', {}).get('date_utc', 'N/A')}")
        print(f"  Format: {match_data.get('match_format', 'N/A')}")
        
        # Check teams
        teams = match_data.get('teams', {})
        team1 = teams.get('team1', {})
        team2 = teams.get('team2', {})
        print(f"  Team 1: {team1.get('name', 'N/A')} ({team1.get('score_overall', 0)})")
        print(f"  Team 2: {team2.get('name', 'N/A')} ({team2.get('score_overall', 0)})")
        
        # Check maps
        maps_data = match_data.get('maps', [])
        print(f"  Maps Played: {len(maps_data)}")
        
        # Check overall player stats
        overall_stats = match_data.get('overall_player_stats', {})
        total_players = sum(len(players) for players in overall_stats.values())
        print(f"  Total Players: {total_players}")
        
        # Show sample player data structure
        if overall_stats:
            print("\n👥 Sample Player Data Structure:")
            for team_name, players in overall_stats.items():
                if players:
                    sample_player = players[0]
                    print(f"  Team: {team_name}")
                    print(f"  Player: {sample_player.get('player_name', 'N/A')}")
                    print(f"  Agent: {sample_player.get('agent', 'N/A')}")
                    
                    # Check if stats are present
                    stats_all = sample_player.get('stats_all_sides', {})
                    stats_attack = sample_player.get('stats_attack', {})
                    stats_defense = sample_player.get('stats_defense', {})
                    
                    print(f"  All Stats Keys: {list(stats_all.keys())}")
                    print(f"  Attack Stats Keys: {list(stats_attack.keys())}")
                    print(f"  Defense Stats Keys: {list(stats_defense.keys())}")
                    break
                break
        
        print("\n✅ Detailed match scraper appears to be working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing detailed scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_detailed_scraper()
