import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from .matches_scraper import MatchesScraper
from .player_stats_scraper import PlayerStatsScraper
from .maps_agents_scraper import MapsAgentsScraper
from .detailed_match_performance_scrapper_v2 import DetailedMatchPerformanceScraper
from .detailed_match_economy_scrapper import DetailedMatchEconomyScraper
from .match_details_scrapper import MatchDetailsScraper

class VLRScraperCoordinator:
    """
    Main coordinator for VLR.gg scraping operations
    Orchestrates the three specialized scrapers: matches, player stats, and maps/agents
    """
    
    def __init__(self):
        self.matches_scraper = MatchesScraper()
        self.stats_scraper = PlayerStatsScraper()
        self.maps_agents_scraper = MapsAgentsScraper()
        self.performance_scraper = DetailedMatchPerformanceScraper()
        self.economy_scraper = DetailedMatchEconomyScraper()
        self.detailed_match_scraper = MatchDetailsScraper()

    def validate_url(self, url: str) -> tuple[bool, str]:
        """Validate VLR.gg event URL"""
        if not url:
            return False, "Please enter a URL"

        if not re.match(r'https?://www\.vlr\.gg/event/\d+/', url):
            return False, "Invalid VLR.gg event URL format. Expected: https://www.vlr.gg/event/{id}/{name}"

        try:
            import requests
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                return True, "Valid URL"
            else:
                return False, f"URL returned status {response.status_code}"
        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"

    def extract_event_info(self, main_url: str) -> Dict[str, Any]:
        """Extract basic event information from main event page"""
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(main_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            event_info = {
                'url': main_url,
                'scraped_at': datetime.now().isoformat()
            }

            # Title
            title_elem = soup.find('h1', class_='wf-title')
            if title_elem:
                event_info['title'] = title_elem.get_text(strip=True)

            # Subtitle
            subtitle_elem = soup.find('h2', class_='event-desc-subtitle')
            if subtitle_elem:
                event_info['subtitle'] = subtitle_elem.get_text(strip=True)

            # Description items
            item_blocks = soup.select('div.event-desc-item')
            for block in item_blocks:
                label = block.find('div', class_='event-desc-item-label')
                value = block.find('div', class_='event-desc-item-value')
                if not label or not value:
                    continue

                label_text = label.get_text(strip=True).lower()
                value_text = value.get_text(strip=True)

                if 'date' in label_text:
                    event_info['dates'] = value_text
                elif 'location' in label_text:
                    event_info['location'] = value_text
                elif 'prize' in label_text:
                    event_info['prize_pool'] = value_text

            return event_info

        except Exception as e:
            return {
                'url': main_url,
                'error': f"Error extracting event info: {e}",
                'scraped_at': datetime.now().isoformat()
            }

    
    def scrape_matches_only(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape only matches data"""
        try:
            if progress_callback:
                progress_callback("Starting matches scraping...")
            
            matches_data = self.matches_scraper.scrape_matches(main_url, progress_callback)
            
            return {
                'event_info': self.extract_event_info(main_url),
                'matches_data': matches_data,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error scraping matches: {e}")
    
    def scrape_player_stats_only(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape only player statistics"""
        try:
            if progress_callback:
                progress_callback("Starting player stats scraping...")
            
            stats_data = self.stats_scraper.scrape_player_stats(main_url, progress_callback)
            
            return {
                'event_info': self.extract_event_info(main_url),
                'stats_data': stats_data,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error scraping player stats: {e}")
    
    def scrape_maps_agents_only(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape only maps and agents data"""
        try:
            if progress_callback:
                progress_callback("Starting maps and agents scraping...")

            maps_agents_data = self.maps_agents_scraper.scrape_maps_and_agents(main_url, progress_callback)

            return {
                'event_info': self.extract_event_info(main_url),
                'maps_agents_data': maps_agents_data,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error scraping maps and agents: {e}")

    def scrape_detailed_match_performance(self, match_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape detailed match performance data (2K, 3K, 4K, 5K, 1v1-1v5, ECON, PL, DE)"""
        try:
            if progress_callback:
                progress_callback(f"Scraping performance data from: {match_url}")

            performance_data = self.performance_scraper.get_match_performance_data(match_url)

            return {
                'match_url': match_url,
                'performance_data': performance_data,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error scraping match performance: {e}")

    def scrape_detailed_match_economy(self, match_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape detailed match economy data"""
        try:
            if progress_callback:
                progress_callback(f"Scraping economy data from: {match_url}")

            economy_data = self.economy_scraper.get_match_economy_data(match_url)

            return {
                'match_url': match_url,
                'economy_data': economy_data,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error scraping match economy: {e}")

    def scrape_detailed_match_performance(self, match_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Scrape detailed match performance data"""
        try:
            if progress_callback:
                progress_callback(f"Scraping performance data from: {match_url}")

            performance_data = self.performance_scraper.get_match_performance_data(match_url)

            return {
                'match_url': match_url,
                'performance_data': performance_data,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error scraping match performance: {e}")

    def _extract_match_urls_from_matches_list(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Extract match URLs from scraped matches list"""
        try:
            match_urls = []

            if isinstance(matches, list):
                for match in matches:
                    if isinstance(match, dict):
                        match_url = match.get('match_url', '')
                        if match_url and match_url.startswith('https://www.vlr.gg/'):
                            match_urls.append(match_url)

            return match_urls

        except Exception as e:
            print(f"⚠️ Error extracting match URLs: {e}")
            return []

    def scrape_comprehensive(self, main_url: str,
                           scrape_matches: bool = True,
                           scrape_stats: bool = True,
                           scrape_maps_agents: bool = True,
                           scrape_economy: bool = False,
                           scrape_detailed_matches: bool = False, # New parameter
                           scrape_detailed_performance: bool = False,
                           scrape_detailed_economy: bool = False,
                           scrape_performance: bool = False,
                           match_urls_for_detailed: List[str] = None,
                           max_matches_limit: int = None,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Scrape comprehensive data using selected scrapers
        """
        try:
            if progress_callback:
                progress_callback("Initializing comprehensive scraping...")
            
            # Initialize result structure
            result = {
                'event_info': {},
                'matches_data': {},
                'stats_data': {},
                'maps_agents_data': {},
                'economy_data': [],
                'detailed_matches': [],
                'performance_data': {},
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract event info
            if progress_callback:
                progress_callback("Extracting event information...")
            result['event_info'] = self.extract_event_info(main_url)
            
            # Scrape matches if requested
            if scrape_matches:
                if progress_callback:
                    progress_callback("Scraping matches data...")
                matches_data = self.matches_scraper.scrape_matches(main_url, progress_callback)
                result['matches_data'] = matches_data

            # Scrape player stats if requested
            if scrape_stats:
                if progress_callback:
                    progress_callback("Scraping player statistics...")
                stats_data = self.stats_scraper.scrape_player_stats(main_url, progress_callback)
                result['stats_data'] = stats_data

            # Scrape maps and agents if requested
            if scrape_maps_agents:
                if progress_callback:
                    progress_callback("Scraping maps and agents data...")
                maps_agents_data = self.maps_agents_scraper.scrape_maps_and_agents(main_url, progress_callback)
                result['maps_agents_data'] = maps_agents_data

            # Scrape economy data if requested
            if scrape_economy:
                if progress_callback:
                    progress_callback("Scraping economy data...")
                if result.get('matches_data', {}).get('matches'):
                    match_urls = [match['match_url'] for match in result['matches_data']['matches']]

                    # Apply limit if specified
                    if max_matches_limit is not None and max_matches_limit != "All":
                        match_urls = match_urls[:max_matches_limit]
                        if progress_callback:
                            progress_callback(f"Limiting economy scraping to {len(match_urls)} matches")

                    economy_data = []
                    for match_url in match_urls:
                        try:
                            if progress_callback:
                                progress_callback(f"Scraping economy for {match_url}")
                            economy_data.append(self.economy_scraper.get_match_economy_data(match_url))
                        except Exception as e:
                            if progress_callback:
                                progress_callback(f"Error scraping economy for {match_url}: {e}")
                    result['economy_data'] = economy_data

            # Extract match URLs for detailed scraping if needed
            if (scrape_detailed_matches or scrape_detailed_performance or scrape_detailed_economy) and not match_urls_for_detailed:
                if progress_callback:
                    progress_callback("Extracting match URLs for detailed scraping...")

                # Extract match URLs from matches data
                matches = result.get('matches_data', {}).get('matches', [])
                match_urls_for_detailed = self._extract_match_urls_from_matches_list(matches)

                # Apply match limit if specified
                if max_matches_limit is not None and max_matches_limit > 0:
                    match_urls_for_detailed = match_urls_for_detailed[:max_matches_limit]
                    if progress_callback:
                        progress_callback(f"Limited to {len(match_urls_for_detailed)} matches for detailed scraping")

                if progress_callback:
                    progress_callback(f"Found {len(match_urls_for_detailed)} match URLs for detailed scraping")

            # Scrape detailed matches if requested
            if scrape_detailed_matches and match_urls_for_detailed:
                if progress_callback:
                    progress_callback("Scraping detailed match data...")

                detailed_matches_results = []
                for i, match_url in enumerate(match_urls_for_detailed):
                    try:
                        if progress_callback:
                            progress_callback(f"Scraping detailed match {i+1}/{len(match_urls_for_detailed)}: {match_url}")

                        match_data = self.detailed_match_scraper.get_match_details(match_url)
                        detailed_matches_results.append(match_data)

                        # Small delay to avoid overwhelming the server
                        import time
                        time.sleep(1)

                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"Error scraping detailed match for {match_url}: {str(e)}")
                        continue

                result['detailed_matches'] = detailed_matches_results

            # Scrape detailed performance data if requested
            if scrape_detailed_performance and match_urls_for_detailed:
                if progress_callback:
                    progress_callback("Scraping detailed match performance data...")

                performance_results = []
                for i, match_url in enumerate(match_urls_for_detailed):
                    try:
                        if progress_callback:
                            progress_callback(f"Scraping performance data {i+1}/{len(match_urls_for_detailed)}: {match_url}")

                        perf_data = self.scrape_detailed_match_performance(match_url, progress_callback)
                        performance_results.append(perf_data)

                        # Small delay to avoid overwhelming the server
                        import time
                        time.sleep(1)

                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"Error scraping performance for {match_url}: {str(e)}")
                        continue

                result['performance_data'] = {
                    'total_matches': len(performance_results),
                    'matches': performance_results
                }

            # Scrape detailed economy data if requested
            if scrape_detailed_economy and match_urls_for_detailed:
                if progress_callback:
                    progress_callback("Scraping detailed match economy data...")

                economy_results = []
                for i, match_url in enumerate(match_urls_for_detailed):
                    try:
                        if progress_callback:
                            progress_callback(f"Scraping economy data {i+1}/{len(match_urls_for_detailed)}: {match_url}")

                        econ_data = self.scrape_detailed_match_economy(match_url, progress_callback)
                        economy_results.append(econ_data)

                        # Small delay to avoid overwhelming the server
                        import time
                        time.sleep(1)

                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"Error scraping economy for {match_url}: {str(e)}")
                        continue

                result['economy_data'] = {
                    'total_matches': len(economy_results),
                    'matches': economy_results
                }

            # Scrape performance data if requested
            if scrape_performance:
                if progress_callback:
                    progress_callback("Scraping performance data...")
                if result.get('matches_data', {}).get('matches'):
                    match_urls = [match['match_url'] for match in result['matches_data']['matches']]

                    # Apply limit if specified
                    if max_matches_limit is not None and max_matches_limit != "All":
                        match_urls = match_urls[:max_matches_limit]
                        if progress_callback:
                            progress_callback(f"Limiting performance scraping to {len(match_urls)} matches")

                    performance_results = []
                    for match_url in match_urls:
                        try:
                            if progress_callback:
                                progress_callback(f"Scraping performance for {match_url}")
                            perf_data = self.performance_scraper.get_match_performance_data(match_url)
                            if perf_data: # Only append if data is not None
                                performance_results.append(perf_data)
                        except Exception as e:
                            if progress_callback:
                                progress_callback(f"Error scraping performance for {match_url}: {e}")
                    result['performance_data'] = {
                        'total_matches': len(performance_results),
                        'matches': performance_results
                    }

            if progress_callback:
                progress_callback("Comprehensive scraping completed!")

            return result
            
        except Exception as e:
            raise Exception(f"Error in comprehensive scraping: {e}")
    
    def get_scraping_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of scraped data"""
        try:
            summary = {
                'event_title': data.get('event_info', {}).get('title', 'Unknown'),
                'total_matches': 0,
                'total_players': 0,
                'total_agents': 0,
                'total_maps': 0,
                'teams_count': 0,
                'detailed_performance_matches': 0,
                'detailed_economy_matches': 0,
                'scraped_sections': []
            }
            
            # Count matches
            matches = data.get('matches_data', {}).get('matches', [])
            if matches:
                summary['total_matches'] = len(matches)
                summary['scraped_sections'].append('Matches')

                # Count unique teams from matches
                teams = set()
                for match in matches:
                    teams.add(match.get('team1', ''))
                    teams.add(match.get('team2', ''))
                teams.discard('')
                summary['teams_count'] = len(teams)

            # Count players
            player_stats = data.get('stats_data', {}).get('player_stats', [])
            if player_stats:
                summary['total_players'] = len(player_stats)
                summary['scraped_sections'].append('Player Stats')

            # Count agents and maps
            agent_utilization = data.get('maps_agents_data', {}).get('agents', [])
            maps = data.get('maps_agents_data', {}).get('maps', [])
            if agent_utilization or maps:
                summary['total_agents'] = len(agent_utilization)
                summary['total_maps'] = len(maps)
                summary['scraped_sections'].append('Maps & Agents')

            # Count economy data
            economy_data = data.get('economy_data', [])
            if economy_data:
                summary['total_economy_records'] = len(economy_data)
                summary['scraped_sections'].append('Economy')

            # Count detailed performance matches
            detailed_performance_data = data.get('detailed_performance_data', {})
            if detailed_performance_data:
                summary['detailed_performance_matches'] = detailed_performance_data.get('total_matches', 0)
                summary['scraped_sections'].append('Detailed Performance')

            # Count detailed economy matches
            detailed_economy_data = data.get('detailed_economy_data', {})
            if detailed_economy_data:
                summary['detailed_economy_matches'] = detailed_economy_data.get('total_matches', 0)
                summary['scraped_sections'].append('Detailed Economy')

            return summary
            
        except Exception:
            return {
                'event_title': 'Unknown',
                'total_matches': 0,
                'total_players': 0,
                'total_agents': 0,
                'total_maps': 0,
                'teams_count': 0,
                'scraped_sections': []
            }
    
    def save_to_json(self, data: Dict[str, Any], filename_prefix: str = 'vlr_data') -> str:
        """Save scraped data to JSON file"""
        try:
            import json
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error saving to JSON: {e}")


# Example usage and testing
if __name__ == "__main__":
    coordinator = VLRScraperCoordinator()
    
    # Test URL
    test_url = "https://www.vlr.gg/event/2097/valorant-champions-2024"
    
    print("🎮 VLR Scraper Coordinator Test")
    print("=" * 50)
    
    try:
        # Validate URL
        is_valid, message = coordinator.validate_url(test_url)
        print(f"URL Validation: {'✅' if is_valid else '❌'} {message}")
        
        if not is_valid:
            exit(1)
        
        def progress_callback(message):
            print(f"📊 {message}")
        
        # Test individual scrapers
        print("\n🧪 Testing Individual Scrapers:")
        print("-" * 30)
        
        # Test matches scraper
        print("1. Testing Matches Scraper...")
        matches_result = coordinator.scrape_matches_only(test_url, progress_callback)
        print(f"   ✅ Matches: {matches_result['matches_data'].get('total_matches', 0)}")
        
        # Test player stats scraper
        print("\n2. Testing Player Stats Scraper...")
        stats_result = coordinator.scrape_player_stats_only(test_url, progress_callback)
        print(f"   ✅ Players: {stats_result['stats_data'].get('total_players', 0)}")
        
        # Test maps/agents scraper
        print("\n3. Testing Maps & Agents Scraper...")
        maps_result = coordinator.scrape_maps_agents_only(test_url, progress_callback)
        print(f"   ✅ Agents: {maps_result['maps_agents_data'].get('total_agents', 0)}")
        print(f"   ✅ Maps: {maps_result['maps_agents_data'].get('total_maps', 0)}")
        
        # Test comprehensive scraping
        print("\n🚀 Testing Comprehensive Scraping:")
        print("-" * 30)
        
        comprehensive_data = coordinator.scrape_comprehensive(
            test_url, 
            scrape_matches=True,
            scrape_stats=True, 
            scrape_maps_agents=True,
            scrape_economy=True,
            progress_callback=progress_callback
        )
        
        # Get summary
        summary = coordinator.get_scraping_summary(comprehensive_data)
        
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   📋 Event: {summary['event_title']}")
        print(f"   🏆 Matches: {summary['total_matches']}")
        print(f"   👥 Players: {summary['total_players']}")
        print(f"   🎭 Agents: {summary['total_agents']}")
        print(f"   🗺️ Maps: {summary['total_maps']}")
        print(f"   💰 Economy Records: {summary.get('total_economy_records', 0)}")
        print(f"   🏅 Teams: {summary['teams_count']}")
        print(f"   📦 Sections: {', '.join(summary['scraped_sections'])}")
        
        # Save data
        filename = coordinator.save_to_json(comprehensive_data)
        print(f"\n💾 Data saved to: {filename}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
