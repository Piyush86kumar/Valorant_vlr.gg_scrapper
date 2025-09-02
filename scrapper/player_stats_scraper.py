import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

class PlayerStatsScraper:
    """
    Dedicated scraper for VLR.gg player statistics
    Handles individual player performance metrics, team affiliations, and rankings
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def construct_stats_url(self, main_url: str) -> str:
        """
        Construct stats URL from main event URL or return if already a stats URL
        Example: https://www.vlr.gg/event/2097/valorant-champions-2024
        -> https://www.vlr.gg/event/stats/2097/valorant-champions-2024
        """
        try:
            # Check if URL is already a stats URL
            if '/event/stats/' in main_url:
                return main_url

            # Extract event ID
            match = re.search(r'/event/(\d+)/', main_url)
            if not match:
                raise ValueError("Could not extract event ID from URL")

            event_id = match.group(1)

            # Extract event name from URL
            url_parts = main_url.split('/')
            event_name = url_parts[-1] if url_parts[-1] else url_parts[-2]

            stats_url = f"https://www.vlr.gg/event/stats/{event_id}/{event_name}"
            return stats_url

        except Exception as e:
            raise ValueError(f"Error constructing stats URL: {e}")

    def scrape_player_stats(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Scrape all player statistics from the stats tab
        """
        try:
            stats_url = self.construct_stats_url(main_url)

            if progress_callback:
                progress_callback("Fetching player stats page...")

            response = self.session.get(stats_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            if progress_callback:
                progress_callback("Parsing player statistics...")

            # Extract player stats from main table
            player_stats = self._extract_player_stats_table(soup, progress_callback)



            result = {
                'players': player_stats,  # Changed from 'player_stats' to 'players' to match UI expectations
                'player_stats': player_stats,  # Keep both for compatibility
                'total_players': len(player_stats),
                'scraped_from': stats_url,
                'scraped_at': datetime.now().isoformat()
            }

            if progress_callback:
                progress_callback(f"Completed! Found {len(player_stats)} players")

            return result

        except Exception as e:
            raise Exception(f"Error scraping player stats: {e}")

    def _extract_player_stats_table(self, soup: BeautifulSoup, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract player statistics from the main stats table"""
        player_stats = []

        # Find the main stats table using correct VLR.gg selector
        stats_table = soup.find('table', class_='wf-table mod-stats mod-scroll')
        if not stats_table:
            # Try alternative selectors
            stats_table = soup.find('table', class_='wf-table-inset')
            if not stats_table:
                stats_table = soup.find('table', class_='stats-table')
                if not stats_table:
                    stats_table = soup.find('table')

        if not stats_table:
            return []

        # Get table rows
        rows = stats_table.find_all('tr')

        # Skip header row and process data rows
        for i, row in enumerate(rows[1:], 1):
            if progress_callback and i % 20 == 0:
                progress_callback(f"Processing player {i}/{len(rows)-1}")

            player_data = self._extract_player_row_vlr(row)
            if player_data:
                player_stats.append(player_data)

        return player_stats

    def _extract_player_row_vlr(self, row) -> Optional[Dict[str, Any]]:
        """Extract player statistics from a VLR.gg table row using correct structure"""
        try:
            cells = row.find_all('td')
            if len(cells) < 21:  # Ensure we have all expected columns
                return None

            player_data = {
                'scraped_at': datetime.now().isoformat()
            }

            # Column 0: Player info (name + team)
            player_cell = cells[0]
            player_link = player_cell.find('a')
            if player_link:
                # Extract player name
                name_elem = player_link.find('div', class_='text-of')
                if name_elem:
                    player_data['player'] = name_elem.get_text(strip=True)
                    player_data['player_name'] = name_elem.get_text(strip=True)  # Keep both for compatibility

                # Extract team
                team_elem = player_link.find('div', class_='stats-player-country')
                if team_elem:
                    player_data['team'] = team_elem.get_text(strip=True)

                # Extract player URL and ID
                href = player_link.get('href', '')
                if href:
                    player_data['player_url'] = f"https://www.vlr.gg{href}" if href.startswith('/') else href

                    # Extract player ID from URL (e.g., /player/8480/aspas -> 8480)
                    import re
                    player_id_match = re.search(r'/player/(\d+)/', href)
                    if player_id_match:
                        player_data['player_id'] = player_id_match.group(1)

            # Column 1: Agents played
            agents_cell = cells[1]
            agents_data = self._extract_agents_played(agents_cell)
            player_data['agents_played'] = agents_data['agents_list']
            player_data['agents_count'] = agents_data['agents_count']
            player_data['agents_display'] = agents_data['agents_display']

            # Column 2: Rounds
            player_data['rounds'] = self._extract_cell_value(cells[2])

            # Column 3: Rating (R2.0)
            player_data['rating'] = self._extract_cell_value(cells[3])

            # Column 4: ACS
            player_data['acs'] = self._extract_cell_value(cells[4])

            # Column 5: K:D
            player_data['kd_ratio'] = self._extract_cell_value(cells[5])

            # Column 6: KAST
            player_data['kast'] = self._extract_cell_value(cells[6])

            # Column 7: ADR
            player_data['adr'] = self._extract_cell_value(cells[7])

            # Column 8: KPR
            player_data['kpr'] = self._extract_cell_value(cells[8])

            # Column 9: APR
            player_data['apr'] = self._extract_cell_value(cells[9])

            # Column 10: FKPR
            player_data['fkpr'] = self._extract_cell_value(cells[10])

            # Column 11: FDPR
            player_data['fdpr'] = self._extract_cell_value(cells[11])

            # Column 12: HS%
            player_data['hs_percent'] = self._extract_cell_value(cells[12])

            # Column 13: CL%
            cl_percent = self._extract_cell_value(cells[13])
            player_data['cl_percent'] = cl_percent if cl_percent and cl_percent != 'N/A' and cl_percent.strip() else '0%'

            # Column 14: CL (clutches)
            player_data['clutches'] = self._extract_cell_value(cells[14])

            # Column 15: KMax
            player_data['k_max'] = self._extract_cell_value(cells[15])

            # Column 16: K (kills)
            player_data['kills'] = self._extract_cell_value(cells[16])

            # Column 17: D (deaths)
            player_data['deaths'] = self._extract_cell_value(cells[17])

            # Column 18: A (assists)
            player_data['assists'] = self._extract_cell_value(cells[18])

            # Column 19: FK (first kills)
            player_data['first_kills'] = self._extract_cell_value(cells[19])

            # Column 20: FD (first deaths)
            player_data['first_deaths'] = self._extract_cell_value(cells[20])

            # Only return if we have essential data
            if player_data.get('player') and player_data.get('team'):
                return player_data

            return None

        except Exception as e:
            return None

    def _extract_cell_value(self, cell) -> str:
        """Extract value from a table cell, handling color-sq structure"""
        try:
            # First try to find value in color-sq span
            color_sq = cell.find('div', class_='color-sq')
            if color_sq:
                span = color_sq.find('span')
                if span:
                    return span.get_text(strip=True)

            # Fallback to direct cell text
            return cell.get_text(strip=True)

        except Exception:
            return 'N/A'

    def _extract_agents_played(self, agents_cell) -> Dict[str, Any]:
        """Extract agents played from the agents cell"""
        try:
            agents_data = {
                'agents_list': [],
                'agents_count': 0,
                'agents_display': 'N/A'
            }

            # Find all agent images
            agent_imgs = agents_cell.find_all('img')
            agents_list = []

            for img in agent_imgs:
                # Extract agent name from src attribute
                src = img.get('src', '')
                if '/agents/' in src:
                    # Extract agent name from path like "/img/vlr/game/agents/jett.png"
                    agent_name = src.split('/agents/')[-1].replace('.png', '').replace('.jpg', '').replace('.webp', '')
                    if agent_name:
                        agents_list.append(agent_name.capitalize())

                # Also try alt attribute
                alt = img.get('alt', '')
                if alt and alt not in agents_list:
                    agents_list.append(alt.capitalize())

            # Check for additional agents indicator like "(+2)"
            cell_text = agents_cell.get_text(strip=True)
            additional_match = re.search(r'\(\+(\d+)\)', cell_text)
            additional_count = 0
            if additional_match:
                additional_count = int(additional_match.group(1))

            # Set the data
            agents_data['agents_list'] = agents_list
            agents_data['agents_count'] = len(agents_list) + additional_count

            # Create display string
            if agents_list:
                display_parts = agents_list.copy()
                if additional_count > 0:
                    display_parts.append(f"(+{additional_count})")
                agents_data['agents_display'] = ', '.join(display_parts)
            else:
                agents_data['agents_display'] = 'N/A'

            return agents_data

        except Exception:
            return {
                'agents_list': [],
                'agents_count': 0,
                'agents_display': 'N/A'
            }

    def _extract_player_row(self, row) -> Optional[Dict[str, Any]]:
        """Extract player statistics from a table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 5:  # Minimum expected columns
                return None

            player_data = {
                'scraped_at': datetime.now().isoformat()
            }

            # Extract player name and team (usually in first cell)
            player_cell = cells[0]

            # Try to find player name
            player_elem = player_cell.find(['div', 'span', 'a'], class_=re.compile(r'player|name'))
            if not player_elem:
                player_elem = player_cell.find('a')
            if not player_elem:
                player_text = player_cell.get_text(strip=True)
                if player_text:
                    player_data['player'] = player_text
            else:
                player_data['player'] = player_elem.get_text(strip=True)

            # Try to find team information
            team_elem = player_cell.find(['img', 'div', 'span'], class_=re.compile(r'team'))
            if team_elem:
                if team_elem.name == 'img':
                    player_data['team'] = team_elem.get('alt', 'Unknown')
                else:
                    player_data['team'] = team_elem.get_text(strip=True)
            else:
                # Try to extract team from player cell text or other cells
                team_link = row.find('a', href=re.compile(r'/team/'))
                if team_link:
                    player_data['team'] = team_link.get_text(strip=True)
                else:
                    player_data['team'] = 'Unknown'

            # Extract statistics from remaining cells
            # Common VLR.gg stats table structure: Player, Rating, ACS, K, D, A, +/-, ADR, HS%, FK, FD
            stats_mapping = [
                ('rating', 1),
                ('acs', 2),
                ('kills', 3),
                ('deaths', 4),
                ('assists', 5),
                ('plus_minus', 6),
                ('adr', 7),
                ('hs_percent', 8),
                ('first_kills', 9),
                ('first_deaths', 10)
            ]

            for stat_name, cell_index in stats_mapping:
                if cell_index < len(cells):
                    value = self._safe_extract_text(cells[cell_index])
                    player_data[stat_name] = value

            # Calculate K/D ratio
            try:
                kills = float(player_data.get('kills', '0'))
                deaths = float(player_data.get('deaths', '1'))
                if deaths > 0:
                    player_data['kd_ratio'] = round(kills / deaths, 2)
                else:
                    player_data['kd_ratio'] = float('inf') if kills > 0 else 0
            except (ValueError, TypeError):
                player_data['kd_ratio'] = 0

            # Calculate KAST if assists are available
            try:
                kills = float(player_data.get('kills', '0'))
                assists = float(player_data.get('assists', '0'))
                # This is a simplified KAST calculation
                player_data['ka_sum'] = kills + assists
            except (ValueError, TypeError):
                player_data['ka_sum'] = 0

            # Only return if we have essential data
            if player_data.get('player'):
                return player_data

            return None

        except Exception as e:
            return None

    def _safe_extract_text(self, cell) -> str:
        """Safely extract text from table cell"""
        try:
            text = cell.get_text(strip=True)
            # Clean up common formatting
            text = text.replace('%', '').replace('+', '').replace('-', '')
            return text if text else '0'
        except:
            return '0'

    def get_top_performers(self, player_stats: List[Dict[str, Any]], metric: str = 'acs', top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top performers by specified metric"""
        try:
            # Filter and sort players by metric
            valid_players = []

            for player in player_stats:
                try:
                    value = float(player.get(metric, '0'))
                    player_copy = player.copy()
                    player_copy[f'{metric}_numeric'] = value
                    valid_players.append(player_copy)
                except (ValueError, TypeError):
                    continue

            # Sort by metric (descending)
            sorted_players = sorted(valid_players, key=lambda x: x[f'{metric}_numeric'], reverse=True)

            return sorted_players[:top_n]

        except Exception:
            return []

    def get_player_rankings(self, player_stats: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Get player rankings across different metrics"""
        try:
            rankings = {}

            metrics = ['acs', 'kills', 'kd_ratio', 'rating', 'adr']

            for metric in metrics:
                rankings[metric] = self.get_top_performers(player_stats, metric, 15)

            return rankings

        except Exception:
            return {}


# Example usage
if __name__ == "__main__":
    scraper = PlayerStatsScraper()

    # Test URL
    test_url = "https://www.vlr.gg/event/2097/valorant-champions-2024"

    print("📊 VLR Player Stats Scraper Test")
    print("=" * 40)

    try:
        def progress_callback(message):
            print(f"📊 {message}")

        # Scrape player stats
        stats_data = scraper.scrape_player_stats(test_url, progress_callback)

        print(f"\n✅ Scraping completed!")
        print(f"   👥 Total players: {stats_data['total_players']}")
        print(f"   🏅 Teams found: {len(stats_data['team_stats'])}")

        # Show sample player
        if stats_data['player_stats']:
            sample = stats_data['player_stats'][0]
            print(f"   🎯 Sample player: {sample.get('player', 'N/A')} ({sample.get('team', 'N/A')})")
            print(f"   📈 ACS: {sample.get('acs', 'N/A')}, K/D: {sample.get('kd_ratio', 'N/A')}")

        # Show top performer
        top_acs = scraper.get_top_performers(stats_data['player_stats'], 'acs', 1)
        if top_acs:
            top_player = top_acs[0]
            print(f"   🏆 Top ACS: {top_player.get('player', 'N/A')} - {top_player.get('acs', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
