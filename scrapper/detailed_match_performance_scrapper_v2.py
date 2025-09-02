#!/usr/bin/env python3
"""
Detailed Match Performance Scraper for VLR.gg (Version 2)
Scrapes the performance tab data including 2K, 3K, 4K, 5K, 1v1-1v5 clutches, ECON, PL, DE
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re

class DetailedMatchPerformanceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_match_performance_data(self, match_url):
        """
        Scrape detailed performance data from a VLR match page
        
        Args:
            match_url (str): URL of the match
            
        Returns:
            dict: Performance data with player statistics
        """
        try:
            # We need to select the "performance" tab. The "game=all" is important.
            if '?' in match_url:
                performance_url = f"{match_url}&game=all&tab=performance"
            else:
                performance_url = f"{match_url}?game=all&tab=performance"
            
            print(f"PERFORMANCE: Scraping performance data from: {performance_url}")
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(performance_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')

            match_id = self._extract_match_id(match_url)
            match_info = self._extract_match_info(soup)
            performance_data = self._extract_performance_data(soup)
            
            result = {
                'match_id': match_id,
                'match_url': match_url,
                'performance_url': performance_url,
                'scraped_at': datetime.now().isoformat(),
                'match_info': match_info,
                'performance_data': performance_data
            }
            
            return result
            
        except Exception as e:
            print(f"ERROR: Error scraping performance data: {e}")
            return None

    def _extract_match_id(self, match_url):
        """Extract match ID from URL"""
        try:
            # Match ID is the number in the URL, e.g., /378822/
            match = re.search(r'/(\d+)/', match_url)
            if match:
                return match.group(1)
            # Fallback for different URL structures
            return match_url.split('/')[3] if len(match_url.split('/')) > 3 else 'unknown'
        except Exception as e:
            print(f"WARNING: Error extracting match ID: {e}")
            return 'unknown'

    def _extract_match_info(self, soup):
        """Extract basic match information from the match header"""
        try:
            match_info = {}
            team_elements = soup.select('.match-header-vs .wf-title-med')
            if len(team_elements) >= 2:
                match_info['team1'] = team_elements[0].get_text(strip=True)
                match_info['team2'] = team_elements[1].get_text(strip=True)
            return match_info
        except Exception as e:
            print(f"WARNING: Error extracting match info: {e}")
            return {}

    def _extract_performance_data(self, soup):
        """Extract detailed performance statistics from all maps"""
        try:
            performance_data = {}
            map_containers = soup.select('div.vm-stats-game[data-game-id]')

            if not map_containers:
                return {}

            map_counter = 1
            for map_container in map_containers:
                game_id = map_container.get('data-game-id', 'unknown')

                if game_id == 'all':
                    continue

                map_name = self._extract_map_name(soup, map_container, map_counter)

                # Find performance tables in this container (tables with 2K, 3K, etc. headers)
                all_tables = map_container.find_all('table')
                perf_tables = []

                for table in all_tables:
                    rows = table.find_all('tr')
                    if len(rows) > 0:
                        header_cells = rows[0].find_all(['th', 'td'])
                        header_text = [cell.get_text(strip=True) for cell in header_cells]
                        if '2K' in header_text and '3K' in header_text and 'ECON' in header_text:
                            perf_tables.append(table)

                # Parse players from the performance table (all players are in one table)
                team1_players = []
                team2_players = []

                if perf_tables:
                    all_players = self._parse_player_rows_from_table(perf_tables[0])

                    # Split players by team (first 5 are usually team1, next 5 are team2)
                    if len(all_players) >= 5:
                        team1_players = all_players[:5]
                        team2_players = all_players[5:10] if len(all_players) >= 10 else []

                if team1_players or team2_players:
                    performance_data[f'map_{map_counter}'] = {
                        'map_name': map_name,
                        'performance_stats': {
                            'team1_players': team1_players,
                            'team2_players': team2_players
                        }
                    }
                    map_counter += 1
            
            return performance_data
        except Exception as e:
            print(f"WARNING: Error extracting performance data: {e}")
            return {}

    def _extract_map_name(self, soup, map_container, map_index=1):
        """Extract map name from a map container"""
        try:
            game_id = map_container['data-game-id']
            map_name_element = soup.select_one(f'.vm-stats-gamesnav-item[data-game-id="{game_id}"]')
            if map_name_element:
                map_name = map_name_element.find('div', style=lambda value: 'margin-bottom: 2px' in value if value else False)
                if map_name:
                    raw_name = map_name.get_text(strip=True).replace('\n', ' ').replace('\t', ' ').strip()
                    # Remove number prefixes like "1Haven" -> "Haven", "2Ascent" -> "Ascent"
                    import re
                    clean_name = re.sub(r'^\d+', '', raw_name).strip()
                    return clean_name if clean_name else raw_name
            return f"Map {map_index}"
        except Exception:
            return f"Map {map_index}"

    def _extract_performance_table(self, map_container):
        """Extract performance stats from both teams in a map"""
        try:
            performance_stats = {'team1_players': [], 'team2_players': []}
            tables = map_container.find_all('table', class_='wf-table-inset')

            if len(tables) >= 1:
                performance_stats['team1_players'] = self._parse_player_rows_from_table(tables[0])
            if len(tables) >= 2:
                performance_stats['team2_players'] = self._parse_player_rows_from_table(tables[1])

            return performance_stats
        except Exception as e:
            print(f"WARNING: Error extracting performance table: {e}")
            return {'team1_players': [], 'team2_players': []}

    def _parse_player_rows_from_table(self, table):
        """Parse all player rows from a table (skip header row)"""
        players = []
        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            player_data = self._extract_player_performance_row(row)
            if player_data:
                players.append(player_data)

        return players

    def _extract_player_performance_row(self, row):
        """Extract performance data from a single player row"""
        try:
            cells = row.find_all('td')
            if not cells or len(cells) < 14:
                return None

            player_cell = cells[0]

            # Extract player name from the team div structure
            team_div = player_cell.find('div', class_='team')
            if not team_div:
                return None

            # Player name is in the nested div structure
            player_name_div = team_div.find('div')
            if not player_name_div:
                return None

            # Get all text and extract player name (before team tag)
            full_text = player_name_div.get_text(strip=True)
            team_tag_div = player_name_div.find('div', class_='team-tag')

            if team_tag_div:
                team_name_from_tag = team_tag_div.get_text(strip=True)
                # Remove team tag from full text to get player name
                player_name = full_text.replace(team_name_from_tag, '').strip()
            else:
                player_name = full_text

            # Player ID removed as requested - not needed for performance analysis

            # Extract team name from team-tag div
            team_name = 'N/A'
            if team_tag_div:
                team_name = team_tag_div.get_text(strip=True)
            else:
                # Fallback: look for team-tag class anywhere in the cell
                team_element = player_cell.find('div', class_='team-tag')
                if team_element:
                    team_name = team_element.get_text(strip=True)

            # Extract agent from the second cell (agent column)
            agent = 'N/A'
            if len(cells) > 1:
                agent_cell = cells[1]
                agent_img = agent_cell.find('img')
                if agent_img and agent_img.has_attr('src'):
                    src = agent_img['src']
                    # Extract agent name from path like "/img/vlr/game/agents/neon.png"
                    agent_match = re.search(r'/agents/([a-zA-Z-]+)\.png', src)
                    if agent_match:
                        agent = agent_match.group(1).capitalize()

            if player_name == 'N/A':
                return None

            return {
                'player_name': player_name,
                'agent': agent,
                'team_name': team_name,
                'multikills': {
                    '2k': self._safe_extract_number(cells[2]),
                    '3k': self._safe_extract_number(cells[3]),
                    '4k': self._safe_extract_number(cells[4]),
                    '5k': self._safe_extract_number(cells[5])
                },
                'clutches': {
                    '1v1': self._safe_extract_number(cells[6]),
                    '1v2': self._safe_extract_number(cells[7]),
                    '1v3': self._safe_extract_number(cells[8]),
                    '1v4': self._safe_extract_number(cells[9]),
                    '1v5': self._safe_extract_number(cells[10])
                },
                'other_stats': {
                    'econ': self._safe_extract_number(cells[11]),
                    'pl': self._safe_extract_number(cells[12]),
                    'de': self._safe_extract_number(cells[13])
                }
            }
        except Exception as e:
            return None

    def _safe_extract_number(self, cell):
        """Safely extract number from table cell with stats-sq div structure"""
        import re  # Import at the top to avoid scope issues
        try:
            # Look for stats-sq div first (VLR.gg structure)
            stats_div = cell.find('div', class_='stats-sq')
            if stats_div:
                # Get all text content from the stats-sq div
                full_text = stats_div.get_text(strip=True)

                # Extract the first number found (this will be the statistic value)
                # The popover content comes after, so the first number is what we want
                match = re.search(r'(\d+)', full_text)
                if match:
                    return int(match.group(1))
                else:
                    # If no number found, it might be empty (0)
                    return 0
            else:
                # Fallback to cell text
                text = cell.get_text(strip=True)
                if not text or text == '-':
                    return 0
                # Extract first number
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
                return 0
        except (ValueError, TypeError):
            return 0
    
    def save_performance_data(self, performance_data, filename=None):
        """Save performance data to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"match_performance_data_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False)
            
            print(f"Performance data saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"ERROR: Error saving performance data: {e}")
            return None

def main():
    """Test the performance scraper"""
    scraper = DetailedMatchPerformanceScraper()
    
    # Test URL
    test_url = "https://www.vlr.gg/378822/drx-vs-sentinels-valorant-champions-2024-ubqf"
    
    print("PERFORMANCE: VLR Detailed Match Performance Scraper v2")
    print("=" * 60)
    
    # Scrape performance data
    performance_data = scraper.get_match_performance_data(test_url)
    
    if performance_data:
        print(f"\nSuccessfully scraped performance data!")
        print(f"Match: {performance_data.get('match_info', {}).get('team1', 'Team1')} vs {performance_data.get('match_info', {}).get('team2', 'Team2')}")

        # Save data
        scraper.save_performance_data(performance_data)
        
        # Display sample data
        print(f"\nPerformance Data Summary:")
        for map_key, map_data in performance_data.get('performance_data', {}).items():
            map_name = map_data.get('map_name', 'Unknown Map')
            stats = map_data.get('performance_stats', {})
            team1_players = stats.get('team1_players', [])
            team2_players = stats.get('team2_players', [])
            
            print(f"  {map_name}")
            print(f"    Team 1: {len(team1_players)} players, Team 2: {len(team2_players)} players")
            
            # Show sample player data from each team
            for i, team_players in enumerate([team1_players, team2_players]):
                if team_players:
                    sample_player = team_players[0]
                    print(f"    SAMPLE (Team {i+1}): {sample_player.get('player_name', 'Unk')} ({sample_player.get('agent', 'Unk')}) - ID: {sample_player.get('player_id', 'N/A')}")
                    print(f"       Multikills: 2K={sample_player['multikills']['2k']}, 3K={sample_player['multikills']['3k']}")
                    print(f"       Clutches: 1v1={sample_player['clutches']['1v1']}, 1v2={sample_player['clutches']['1v2']}")
        
        print(f"\nSUCCESS: Performance scraping complete!")

    else:
        print(f"\nERROR: Failed to scrape performance data")

if __name__ == "__main__":
    main()