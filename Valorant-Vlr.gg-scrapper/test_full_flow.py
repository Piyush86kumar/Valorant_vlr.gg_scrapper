#!/usr/bin/env python3
"""
Test the complete flow from event URL to performance/economy data
"""

from vlr_scraper_coordinator import VLRScraperCoordinator

def test_complete_flow():
    """Test the complete scraping flow"""
    print("🧪 Testing Complete VLR Scraping Flow")
    print("=" * 60)
    
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
    
    if result:
        print("✅ Scraping completed successfully!")
        
        # Check basic data
        matches = result.get('matches', [])
        player_stats = result.get('player_stats', [])
        print(f"📊 Basic data: {len(matches)} matches, {len(player_stats)} player stats")
        
        # Check detailed matches
        detailed_matches = result.get('detailed_matches', [])
        print(f"🔍 Detailed matches: {len(detailed_matches)}")
        
        # Check performance data
        performance_data = result.get('performance_data', {})
        if performance_data and performance_data.get('matches'):
            perf_matches = performance_data['matches']
            print(f"🎯 Performance data: {len(perf_matches)} matches")
            
            # Show sample performance data
            if perf_matches:
                sample_match = perf_matches[0]
                perf_data = sample_match.get('performance_data', {})
                if perf_data and isinstance(perf_data, dict):
                    first_map_key = list(perf_data.keys())[0] if perf_data else None
                    if first_map_key:
                        first_map = perf_data[first_map_key]
                        if isinstance(first_map, dict):
                            team1_count = len(first_map.get('team1_players', []))
                            team2_count = len(first_map.get('team2_players', []))
                            print(f"   Sample match: Team1={team1_count} players, Team2={team2_count} players")

                            if team1_count > 0:
                                sample_player = first_map['team1_players'][0]
                                player_name = sample_player.get('player_name', 'Unknown')
                                multikills = sample_player.get('multikills', {})
                                print(f"   Sample player: {player_name} - 2K: {multikills.get('2k', 0)}, 3K: {multikills.get('3k', 0)}")
        else:
            print("❌ No performance data found")
        
        # Check economy data
        economy_data = result.get('economy_data', {})
        if economy_data and economy_data.get('matches'):
            econ_matches = economy_data['matches']
            print(f"💰 Economy data: {len(econ_matches)} matches")
            
            # Show sample economy data
            if econ_matches:
                sample_match = econ_matches[0]
                econ_data = sample_match.get('economy_data', {})
                if econ_data:
                    first_map = list(econ_data.values())[0]
                    team_economy = first_map.get('team_economy', {})
                    if team_economy:
                        team1 = team_economy.get('team1', {})
                        team2 = team_economy.get('team2', {})
                        team1_name = team1.get('team_name', 'Team1')
                        team2_name = team2.get('team_name', 'Team2')
                        print(f"   Sample match: {team1_name} vs {team2_name}")
                        
                        if team1.get('metrics'):
                            pistol_won = team1['metrics'].get('Pistol Won', 'N/A')
                            eco_won = team1['metrics'].get('Eco (won)', 'N/A')
                            print(f"   {team1_name}: Pistol Won={pistol_won}, Eco Won={eco_won}")
        else:
            print("❌ No economy data found")
        
        print("\n✅ Test completed successfully!")
        return True
        
    else:
        print("❌ Scraping failed!")
        return False

if __name__ == "__main__":
    test_complete_flow()
