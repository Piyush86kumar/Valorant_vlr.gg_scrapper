import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

class MapsAgentsScraper:
    """
    Dedicated scraper for VLR.gg maps and agents data
    Handles separate extraction of maps statistics and agent utilization data
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def construct_agents_url(self, main_url: str) -> str:
        """
        Construct agents URL from main event URL or return if already an agents URL
        Example: https://www.vlr.gg/event/2097/valorant-champions-2024
        -> https://www.vlr.gg/event/agents/2097/valorant-champions-2024
        """
        try:
            # Check if URL is already an agents URL
            if '/event/agents/' in main_url:
                return main_url

            # Extract event ID
            match = re.search(r'/event/(\d+)/', main_url)
            if not match:
                raise ValueError("Could not extract event ID from URL")

            event_id = match.group(1)

            # Extract event name from URL
            url_parts = main_url.split('/')
            event_name = url_parts[-1] if url_parts[-1] else url_parts[-2]

            agents_url = f"https://www.vlr.gg/event/agents/{event_id}/{event_name}"
            return agents_url

        except Exception as e:
            raise ValueError(f"Error constructing agents URL: {e}")

    def scrape_maps_and_agents(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Scrape maps and agents data from the agents tab - returns separate maps and agents data
        """
        try:
            agents_url = self.construct_agents_url(main_url)

            if progress_callback:
                progress_callback("Fetching maps and agents page...")

            response = self.session.get(agents_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            if progress_callback:
                progress_callback("Parsing maps and agents data...")

            # Extract maps data from the first table (global overview)
            maps_data = self._extract_maps_data_vlr(soup, progress_callback)

            # Extract agents utilization data from the first table
            agents_data = self._extract_agents_data_vlr(soup, progress_callback)

            # Extract match ID from URL
            match_id = None
            match = re.search(r'/(\d+)/', main_url)
            if match:
                match_id = match.group(1)

            result = {
                'maps': maps_data,
                'agents': agents_data,
                'total_maps': len(maps_data),
                'total_agents': len(agents_data),
                'scraped_from': agents_url,
                'match_id': match_id
            }

            if progress_callback:
                progress_callback(f"Completed! Found {len(maps_data)} maps, {len(agents_data)} agents")

            return result

        except Exception as e:
            raise Exception(f"Error scraping maps and agents: {e}")

    def _extract_maps_data_vlr(self, soup: BeautifulSoup, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract maps data from the first table (global overview)"""
        maps_data = []

        try:
            # Find the first table with class 'wf-table mod-pr-global'
            global_table = soup.find('table', class_='wf-table mod-pr-global')
            if not global_table:
                return []

            # Get all rows except header
            rows = global_table.find_all('tr', class_='pr-global-row')

            for i, row in enumerate(rows):
                if progress_callback and i % 5 == 0:
                    progress_callback(f"Processing map {i+1}/{len(rows)}")

                map_data = self._extract_map_row_vlr(row)
                if map_data:
                    maps_data.append(map_data)

            return maps_data

        except Exception as e:
            return []

    def _extract_map_row_vlr(self, row) -> Optional[Dict[str, Any]]:
        """Extract map data from a VLR.gg table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 4:
                return None

            map_data = {}

            # Column 0: Map name
            map_cell = cells[0]
            map_text = map_cell.get_text(strip=True)
            # Remove the pseudo-icon letter (e.g., "A Ascent" -> "Ascent", "IIcebox" -> "Icebox")
            if len(map_text) > 2 and map_text[1] == ' ':
                map_data['map_name'] = map_text[2:]
            elif len(map_text) > 1 and map_text[0] == map_text[1]:
                # Handle cases like "IIcebox" -> "Icebox"
                map_data['map_name'] = map_text[1:]
            else:
                map_data['map_name'] = map_text

            # Skip if map name is empty or just whitespace
            if not map_data['map_name'] or not map_data['map_name'].strip():
                return None

            # Column 1: Number of times played
            map_data['times_played'] = cells[1].get_text(strip=True)

            # Column 2: Attack win percentage
            map_data['attack_win_percent'] = cells[2].get_text(strip=True)

            # Column 3: Defense win percentage
            map_data['defense_win_percent'] = cells[3].get_text(strip=True)

            return map_data if map_data.get('map_name') else None

        except Exception as e:
            return None

    def _extract_agents_data_vlr(self, soup: BeautifulSoup, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract agents utilization data exactly as shown on VLR.gg - total utilization + individual map utilizations"""
        agents_data = []

        try:
            # Find the first table with class 'wf-table mod-pr-global'
            global_table = soup.find('table', class_='wf-table mod-pr-global')
            if not global_table:
                return []

            # Get all rows
            rows = global_table.find_all('tr')
            if not rows:
                return []

            # Get header row to extract map names
            header_row = rows[0]
            header_cells = header_row.find_all('th')
            
            # Extract map names from first 4 columns
            map_names = []
            for cell in header_cells[:4]:
                map_name = cell.get_text(strip=True)
                if map_name and map_name not in ['Map', '#', 'ATK WIN', 'DEF WIN']:
                    map_names.append(map_name)

            # Get agent headers (columns 4 onwards contain agent images)
            agent_headers = header_cells[4:]  # Skip first 4 columns (Map, #, ATK WIN, DEF WIN)

            # Extract agent names from header images
            agent_names = []
            for header in agent_headers:
                img = header.find('img')
                if img and img.get('src'):
                    src = img.get('src')
                    if '/agents/' in src:
                        agent_name = src.split('/agents/')[-1].replace('.png', '').replace('.jpg', '').replace('.webp', '')
                        agent_names.append(agent_name.capitalize())
                    else:
                        agent_names.append('Unknown')
                else:
                    agent_names.append('Unknown')

            # Get all data rows
            data_rows = global_table.find_all('tr', class_='pr-global-row')

            # Extract agent utilization data exactly as VLR.gg shows it
            for i, agent_name in enumerate(agent_names):
                if progress_callback and i % 10 == 0:
                    progress_callback(f"Processing agent {i+1}/{len(agent_names)}")

                agent_data = {
                    'agent_name': agent_name,
                    'total_utilization': 0.0,
                    'map_utilizations': {}
                }

                # Initialize map utilizations for each map
                for map_name in map_names:
                    agent_data['map_utilizations'][map_name] = 0.0

                # Extract total utilization (first row) and individual map utilizations
                for row_idx, row in enumerate(data_rows):
                    cells = row.find_all('td')
                    if len(cells) > (4 + i):  # Ensure we have the agent column
                        agent_cell = cells[4 + i]
                        color_sq = agent_cell.find('div', class_='color-sq')
                        if color_sq:
                            span = color_sq.find('span')
                            if span:
                                util_text = span.get_text(strip=True)
                                try:
                                    util_percent = float(util_text.replace('%', ''))

                                    # Check if this is the total row (first row with class 'mod-all' or empty map name)
                                    map_cell = cells[0]
                                    map_text = map_cell.get_text(strip=True)

                                    if not map_text or 'mod-all' in row.get('class', []):
                                        # This is the total utilization row
                                        agent_data['total_utilization'] = util_percent
                                    else:
                                        # This is an individual map row
                                        # Clean map name
                                        if len(map_text) > 2 and map_text[1] == ' ':
                                            map_name = map_text[2:]
                                        elif len(map_text) > 1 and map_text[0] == map_text[1]:
                                            # Handle cases like "IIcebox" -> "Icebox"
                                            map_name = map_text[1:]
                                        else:
                                            map_name = map_text

                                        # Only add if map name is not empty
                                        if map_name and map_name.strip():
                                            agent_data['map_utilizations'][map_name] = util_percent
                                except ValueError:
                                    pass

                agents_data.append(agent_data)

            return agents_data

        except Exception as e:
            print(f"Error extracting agents data: {str(e)}")
            return []

    def _extract_agent_usage(self, table) -> Dict[str, Any]:
        """Extract agent usage statistics from the table"""
        try:
            # Get all rows except header
            rows = table.find_all('tr')[1:]  # Skip header row
            
            # Initialize data structure
            agent_data = {
                'agent_name': '',
                'pick_rate': 0.0,
                'win_rate': 0.0,
                'map_utilizations': []
            }
            
            # Process each row
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # Ensure we have enough cells
                    # Extract agent name
                    agent_name_elem = cells[0].find('div', class_='text-of')
                    if agent_name_elem:
                        agent_data['agent_name'] = agent_name_elem.text.strip()
                    
                    # Extract pick rate
                    pick_rate_elem = cells[1].find('div', class_='text-of')
                    if pick_rate_elem:
                        pick_rate_text = pick_rate_elem.text.strip().rstrip('%')
                        try:
                            agent_data['pick_rate'] = float(pick_rate_text)
                        except ValueError:
                            agent_data['pick_rate'] = 0.0
                    
                    # Extract win rate
                    win_rate_elem = cells[2].find('div', class_='text-of')
                    if win_rate_elem:
                        win_rate_text = win_rate_elem.text.strip().rstrip('%')
                        try:
                            agent_data['win_rate'] = float(win_rate_text)
                        except ValueError:
                            agent_data['win_rate'] = 0.0
                    
                    # Extract map utilizations
                    map_utilizations = []
                    map_cells = cells[3].find_all('div', class_='text-of')
                    for map_cell in map_cells:
                        map_text = map_cell.text.strip()
                        if map_text:
                            # Extract map name and utilization
                            parts = map_text.split(' ')
                            if len(parts) >= 2:
                                map_name = ' '.join(parts[:-1])  # All parts except the last one
                                utilization = parts[-1].rstrip('%')
                                try:
                                    map_utilizations.append({
                                        'map_name': map_name,
                                        'utilization': float(utilization)
                                    })
                                except ValueError:
                                    continue
                    
                    agent_data['map_utilizations'] = map_utilizations
            
            return agent_data
            
        except Exception as e:
            print(f"Error extracting agent usage: {str(e)}")
            return {
                'agent_name': '',
                'pick_rate': 0.0,
                'win_rate': 0.0,
                'map_utilizations': []
            }

    def _extract_agent_row(self, row) -> Optional[Dict[str, Any]]:
        """Extract agent statistics from a table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 3:  # Minimum expected columns
                return None

            agent_data = {
                'scraped_at': datetime.now().isoformat()
            }

            # Extract agent name (first cell)
            agent_cell = cells[0]

            # Try to find agent image first
            agent_img = agent_cell.find('img')
            if agent_img:
                # Get agent name from alt text or src
                agent_name = agent_img.get('alt', '')
                if not agent_name and agent_img.get('src'):
                    src = agent_img.get('src')
                    if '/agents/' in src:
                        agent_name = src.split('/agents/')[-1].split('.')[0].title()
                        agent_name = agent_name.replace('_', ' ').replace('-', ' ')
                agent_data['agent'] = agent_name

            # If no image, try text
            if 'agent' not in agent_data or not agent_data['agent']:
                agent_text = agent_cell.get_text(strip=True)
                if agent_text:
                    agent_data['agent'] = agent_text

            if not agent_data.get('agent'):
                return None

            # Extract usage statistics
            # Common structure: Agent, Usage Count, Usage %, Win Rate, Avg Rating, Avg ACS
            stats_mapping = [
                ('usage_count', 1),
                ('usage_percentage', 2),
                ('win_rate', 3),
                ('avg_rating', 4),
                ('avg_acs', 5),
                ('pick_rate', 6),
                ('ban_rate', 7)
            ]

            for stat_name, cell_index in stats_mapping:
                if cell_index < len(cells):
                    value = self._safe_extract_text(cells[cell_index])
                    agent_data[stat_name] = value

            # Calculate additional metrics
            try:
                usage_count = int(agent_data.get('usage_count', '0'))
                agent_data['usage_count_numeric'] = usage_count

                # Extract percentage value
                usage_pct = agent_data.get('usage_percentage', '0%')
                usage_pct_clean = float(usage_pct.replace('%', ''))
                agent_data['usage_percentage_numeric'] = usage_pct_clean

                # Extract win rate
                win_rate = agent_data.get('win_rate', '0%')
                win_rate_clean = float(win_rate.replace('%', ''))
                agent_data['win_rate_numeric'] = win_rate_clean

            except (ValueError, TypeError):
                agent_data['usage_count_numeric'] = 0
                agent_data['usage_percentage_numeric'] = 0
                agent_data['win_rate_numeric'] = 0

            return agent_data

        except Exception as e:
            return None

    def _extract_map_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract map statistics if available"""
        try:
            map_stats = []

            # Look for map-related tables or sections
            map_sections = soup.find_all(['table', 'div'], class_=re.compile(r'map'))

            for section in map_sections:
                if section.name == 'table':
                    # Process map table
                    rows = section.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        map_data = self._extract_map_row(row)
                        if map_data:
                            map_stats.append(map_data)
                else:
                    # Process map section
                    map_elements = section.find_all(['div', 'span'], class_=re.compile(r'map.*name'))
                    for elem in map_elements:
                        map_name = elem.get_text(strip=True)
                        if map_name and len(map_name) < 50:  # Reasonable map name length
                            map_stats.append({
                                'map': map_name,
                                'scraped_at': datetime.now().isoformat()
                            })

            return map_stats

        except Exception:
            return []

    def _extract_map_row(self, row) -> Optional[Dict[str, Any]]:
        """Extract map statistics from a table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 2:
                return None

            map_data = {
                'scraped_at': datetime.now().isoformat()
            }

            # Extract map name
            map_cell = cells[0]
            map_img = map_cell.find('img')
            if map_img:
                map_name = map_img.get('alt', '')
                if not map_name and map_img.get('src'):
                    src = map_img.get('src')
                    if '/maps/' in src:
                        map_name = src.split('/maps/')[-1].split('.')[0].title()
                map_data['map'] = map_name
            else:
                map_data['map'] = map_cell.get_text(strip=True)

            # Extract map statistics
            stats_mapping = [
                ('pick_count', 1),
                ('pick_rate', 2),
                ('win_rate_attack', 3),
                ('win_rate_defense', 4),
                ('avg_rounds', 5)
            ]

            for stat_name, cell_index in stats_mapping:
                if cell_index < len(cells):
                    value = self._safe_extract_text(cells[cell_index])
                    map_data[stat_name] = value

            return map_data if map_data.get('map') else None

        except Exception:
            return None

    def _safe_extract_text(self, cell) -> str:
        """Safely extract text from table cell"""
        try:
            text = cell.get_text(strip=True)
            return text if text else '0'
        except:
            return '0'

    def _analyze_meta(self, agent_stats: List[Dict[str, Any]], map_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze meta trends from agent and map data"""
        try:
            meta_analysis = {
                'top_agents': [],
                'agent_roles': {},
                'pick_ban_trends': {},
                'map_preferences': []
            }

            # Analyze top agents by usage
            sorted_agents = sorted(agent_stats, key=lambda x: x.get('usage_percentage_numeric', 0), reverse=True)
            meta_analysis['top_agents'] = sorted_agents[:10]

            # Categorize agents by role (basic categorization)
            role_mapping = {
                'jett': 'Duelist',
                'reyna': 'Duelist',
                'phoenix': 'Duelist',
                'raze': 'Duelist',
                'yoru': 'Duelist',
                'neon': 'Duelist',
                'iso': 'Duelist',
                'sage': 'Sentinel',
                'cypher': 'Sentinel',
                'killjoy': 'Sentinel',
                'chamber': 'Sentinel',
                'deadlock': 'Sentinel',
                'sova': 'Initiator',
                'breach': 'Initiator',
                'skye': 'Initiator',
                'kayo': 'Initiator',
                'fade': 'Initiator',
                'gekko': 'Initiator',
                'omen': 'Controller',
                'brimstone': 'Controller',
                'viper': 'Controller',
                'astra': 'Controller',
                'harbor': 'Controller',
                'clove': 'Controller'
            }

            for agent in agent_stats:
                agent_name = agent.get('agent', '').lower()
                role = role_mapping.get(agent_name, 'Unknown')

                if role not in meta_analysis['agent_roles']:
                    meta_analysis['agent_roles'][role] = []

                meta_analysis['agent_roles'][role].append({
                    'agent': agent.get('agent'),
                    'usage_percentage': agent.get('usage_percentage_numeric', 0),
                    'win_rate': agent.get('win_rate_numeric', 0)
                })

            # Sort agents within each role
            for role in meta_analysis['agent_roles']:
                meta_analysis['agent_roles'][role].sort(key=lambda x: x['usage_percentage'], reverse=True)

            # Analyze map preferences
            if map_stats:
                sorted_maps = sorted(map_stats, key=lambda x: float(x.get('pick_rate', '0').replace('%', '')), reverse=True)
                meta_analysis['map_preferences'] = sorted_maps[:7]  # Top 7 maps

            return meta_analysis

        except Exception:
            return {
                'top_agents': [],
                'agent_roles': {},
                'pick_ban_trends': {},
                'map_preferences': []
            }

    def get_agent_meta_summary(self, agent_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a summary of the agent meta"""
        try:
            summary = {
                'most_picked': None,
                'highest_winrate': None,
                'most_contested': None,
                'total_picks': 0
            }

            if not agent_stats:
                return summary

            # Most picked agent
            most_picked = max(agent_stats, key=lambda x: x.get('usage_count_numeric', 0))
            summary['most_picked'] = {
                'agent': most_picked.get('agent'),
                'usage_count': most_picked.get('usage_count'),
                'usage_percentage': most_picked.get('usage_percentage')
            }

            # Highest win rate agent (with minimum usage threshold)
            high_usage_agents = [a for a in agent_stats if a.get('usage_count_numeric', 0) >= 5]
            if high_usage_agents:
                highest_wr = max(high_usage_agents, key=lambda x: x.get('win_rate_numeric', 0))
                summary['highest_winrate'] = {
                    'agent': highest_wr.get('agent'),
                    'win_rate': highest_wr.get('win_rate'),
                    'usage_count': highest_wr.get('usage_count')
                }

            # Total picks
            summary['total_picks'] = sum(a.get('usage_count_numeric', 0) for a in agent_stats)

            return summary

        except Exception:
            return {
                'most_picked': None,
                'highest_winrate': None,
                'most_contested': None,
                'total_picks': 0
            }


# Example usage
if __name__ == "__main__":
    scraper = MapsAgentsScraper()

    # Test URL
    test_url = "https://www.vlr.gg/event/2097/valorant-champions-2024"

    print("🎭 VLR Maps & Agents Scraper Test")
    print("=" * 40)

    try:
        def progress_callback(message):
            print(f"📊 {message}")

        # Scrape maps and agents
        data = scraper.scrape_maps_and_agents(test_url, progress_callback)

        print(f"\n✅ Scraping completed!")
        print(f"   🎭 Total agents: {data['total_agents']}")
        print(f"   🗺️ Total maps: {data['total_maps']}")

        # Show sample agent
        if data['agent_stats']:
            sample = data['agent_stats'][0]
            print(f"   🎯 Sample agent: {sample.get('agent', 'N/A')} - {sample.get('usage_percentage', 'N/A')}")

        # Show meta summary
        meta_summary = scraper.get_agent_meta_summary(data['agent_stats'])
        if meta_summary['most_picked']:
            most_picked = meta_summary['most_picked']
            print(f"   🏆 Most picked: {most_picked['agent']} ({most_picked['usage_percentage']})")

        print(f"   📊 Total agent picks: {meta_summary['total_picks']}")

    except Exception as e:
        print(f"❌ Error: {e}")
