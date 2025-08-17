#!/usr/bin/env python3
"""
Detailed Match Economy Scraper for VLR.gg
Scrapes the economy tab data including team-level economy statistics
Extracts data in format: Pistol Won | Eco (won) | $ (won) | $$ (won) | $$$ (won)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import re

class DetailedMatchEconomyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_match_economy_data(self, match_url):
        """
        Scrape detailed economy data from a VLR match page for all maps and individual maps

        Args:
            match_url (str): URL of the match (e.g., https://www.vlr.gg/378663/funplus-phoenix-vs-team-heretics-valorant-champions-2024-opening-b/)

        Returns:
            dict: Economy data with team-level economic statistics for all maps and individual maps
        """
        try:
            # Extract match ID from URL
            match_id = self._extract_match_id(match_url)

            # Get all economy data from the main economy page which contains all tables
            economy_data = self._scrape_all_economy_tables(match_url)

            # Add match ID to all records
            for team_data in economy_data:
                team_data['match_id'] = match_id

            result = {
                'match_url': match_url,
                'match_id': match_id,
                'scraped_at': datetime.now().isoformat(),
                'economy_data': economy_data
            }

            return result

        except Exception as e:
            print(f"ERROR: Error scraping economy data: {e}")
            return None

    def _scrape_all_economy_tables(self, match_url):
        """
        Scrape all economy tables from the main economy page

        Args:
            match_url (str): Base match URL

        Returns:
            list: List of all economy data for all maps
        """
        try:
            # Construct economy URL for all maps
            if '?' in match_url:
                economy_url = f"{match_url}&game=all&tab=economy"
            else:
                economy_url = f"{match_url}?game=all&tab=economy"

            print(f"ECONOMY: Scraping all economy data from: {economy_url}")

            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))

            response = self.session.get(economy_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all economy tables on the page
            tables = soup.find_all('table')
            economy_tables = []

            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue

                header_texts = [th.get_text(strip=True) for th in headers]

                # Look for the specific economy table headers we need
                if any(header in header_texts for header in ['Pistol Won', 'Eco', '$', '$$', '$$$']):
                    economy_tables.append(table)

            print(f"ECONOMY: Found {len(economy_tables)} economy tables on the page")

            # Parse each economy table and determine which map it belongs to
            all_economy_data = []

            # Dynamically detect map names from the page
            map_names = self._extract_map_names_from_page(soup)
            print(f"ECONOMY: Processing {len(economy_tables)} economy tables for maps: {map_names}")

            for i, table in enumerate(economy_tables):
                if i < len(map_names):
                    map_name = map_names[i]
                    # Extract data from this table
                    table_data = self._extract_team_economy_data_from_table(table, map_name)
                    all_economy_data.extend(table_data)
                else:
                    print(f"WARNING: Extra table found (index {i}), skipping")

            return all_economy_data

        except Exception as e:
            print(f"WARNING: Error scraping all economy tables: {e}")
            return []

    def _extract_map_names_from_page(self, soup):
        """
        Extract map names from the economy page navigation/tabs

        Args:
            soup: BeautifulSoup object of the economy page

        Returns:
            list: List of map names in the order they appear
        """
        try:
            map_names = ["All Maps"]  # First table is always "All Maps"

            # Look for map navigation tabs or links
            # VLR.gg has navigation like "All Maps", "1 Haven", "2 Ascent", "3 Abyss"

            # Method 1: Look for numbered map links in navigation
            map_links = soup.find_all('a', href=lambda href: href and 'game=' in href and 'tab=economy' in href)

            # Sort links by the number in their text to maintain order
            numbered_maps = []
            for link in map_links:
                link_text = link.get_text(strip=True)
                # Extract map name from text like "1 Haven", "2 Ascent", etc.
                if link_text and len(link_text) > 1 and link_text[0].isdigit():
                    map_number = int(link_text[0])
                    map_name = link_text[2:].strip()  # Remove "1 " prefix
                    if map_name:
                        numbered_maps.append((map_number, map_name))

            # Sort by map number and add to map_names
            numbered_maps.sort(key=lambda x: x[0])
            for _, map_name in numbered_maps:
                if map_name not in map_names:
                    map_names.append(map_name)

            # If no numbered maps found, look for any text containing map names
            if len(map_names) == 1:
                # Look for the ban/pick text which shows which maps were played
                ban_pick_elements = soup.find_all(string=lambda text: text and ('pick' in text.lower() or 'ban' in text.lower()))
                picked_maps = []
                for element in ban_pick_elements:
                    text = element.strip()
                    if 'pick' in text.lower() and 'ban' in text.lower():
                        # Extract played maps from ban/pick text
                        # Format: "SEN ban Icebox; GEN ban Sunset; SEN pick Haven; GEN pick Ascent; SEN ban Bind; GEN ban Lotus; Abyss remains"
                        if 'pick' in text:
                            import re
                            picks = re.findall(r'pick\s+([A-Za-z]+)', text)
                            for pick in picks:
                                if pick not in picked_maps:
                                    picked_maps.append(pick)

                # Based on the HTML structure, the tables appear in this order:
                # Table 1: First picked map (Haven)
                # Table 2: Second picked map (Ascent)
                # Table 3: All Maps (aggregate)
                # So we need to reorder: [All Maps, Haven, Ascent] -> [Haven, Ascent, All Maps]
                if len(picked_maps) >= 2:
                    map_names = picked_maps + ["All Maps"]  # Individual maps first, then aggregate

            return map_names

        except Exception as e:
            print(f"WARNING: Error extracting map names: {e}")
            # Fallback to default order
            return ["All Maps", "Map 1", "Map 2", "Map 3"]

    def _extract_match_id(self, match_url):
        """Extract match ID from URL"""
        try:
            match = re.search(r'/(\d+)/', match_url)
            return match.group(1) if match else None
        except:
            return None

    def _scrape_economy_for_game(self, match_url, game_id, map_name):
        """
        Scrape economy data for a specific game (all maps or individual map)

        Args:
            match_url (str): Base match URL
            game_id (str): Game ID ("all" for all maps, or specific game ID for individual map)
            map_name (str): Name of the map

        Returns:
            list: List of team economy data dictionaries
        """
        try:
            # Construct economy URL
            if '?' in match_url:
                economy_url = f"{match_url}&game={game_id}&tab=economy"
            else:
                economy_url = f"{match_url}?game={game_id}&tab=economy"

            print(f"ECONOMY: Scraping economy data from: {economy_url}")

            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))

            response = self.session.get(economy_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract team economy data
            return self._extract_team_economy_data(soup, map_name)

        except Exception as e:
            print(f"WARNING: Error scraping economy for game {game_id}: {e}")
            return []

    def _scrape_individual_maps_economy(self, match_url):
        """
        Scrape economy data for individual maps by discovering map game IDs

        Args:
            match_url (str): Base match URL

        Returns:
            list: List of economy data for each individual map
        """
        try:
            # First, get the match page to discover individual map game IDs
            response = self.session.get(match_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find map sections to get game IDs and map names
            map_sections = soup.select('div.vm-stats-container > div.vm-stats-game[data-game-id]:not([data-game-id="all"])')

            individual_maps_data = []

            for map_section in map_sections:
                game_id = map_section.get('data-game-id')

                # Extract map name
                map_name = "Unknown Map"
                header = map_section.find('div', class_='vm-stats-game-header')
                if header:
                    map_info_div = header.find('div', class_='map')
                    if map_info_div:
                        map_name_container = map_info_div.find('div', style=lambda x: x and 'font-weight: 700' in x)
                        if map_name_container:
                            map_name_span = map_name_container.find('span')
                            if map_name_span:
                                map_name = map_name_span.get_text(strip=True).replace('PICK', '').strip()

                if game_id:
                    print(f"🗺️ Found map: {map_name} (Game ID: {game_id})")
                    map_economy_data = self._scrape_economy_for_game(match_url, game_id, map_name)
                    if map_economy_data:
                        individual_maps_data.append(map_economy_data)

            return individual_maps_data

        except Exception as e:
            print(f"WARNING: Error scraping individual maps economy: {e}")
            return []

    def _extract_team_economy_data(self, soup, map_name):
        """
        Extract team-level economy data from the economy page

        Args:
            soup: BeautifulSoup object of the economy page
            map_name (str): Name of the map

        Returns:
            list: List of team economy data dictionaries
        """
        try:
            team_economy_data = []

            # Find all tables with economy data
            tables = soup.find_all('table')

            economy_table = None

            # For "All Maps", we want the FIRST economy table (summary table)
            if map_name == "All Maps":
                for table in tables:
                    headers = table.find_all('th')
                    if not headers:
                        continue

                    header_texts = [th.get_text(strip=True) for th in headers]

                    # Look for the specific economy table headers we need
                    if any(header in header_texts for header in ['Pistol Won', 'Eco', '$', '$$', '$$$']):
                        print(f"ECONOMY: Found 'All Maps' economy table with headers: {header_texts}")
                        economy_table = table
                        break  # Take the FIRST economy table for All Maps
            else:
                # For individual maps, we need to find the correct table by looking at the context
                # The page shows multiple economy tables, we need to find the one that matches our map

                # First, find all economy tables
                economy_tables_found = []
                for table in tables:
                    headers = table.find_all('th')
                    if not headers:
                        continue

                    header_texts = [th.get_text(strip=True) for th in headers]

                    # Look for the specific economy table headers we need
                    if any(header in header_texts for header in ['Pistol Won', 'Eco', '$', '$$', '$$$']):
                        economy_tables_found.append(table)

                print(f"ECONOMY: Found {len(economy_tables_found)} economy tables on the page")

                # Now we need to identify which table corresponds to which map
                # Look for map indicators in the page structure around each table
                for i, table in enumerate(economy_tables_found):
                    # Check if this table is preceded by a map indicator
                    table_context = self._get_table_context(table, soup)
                    print(f"ECONOMY: Table #{i+1} context: {table_context}")

                    # For "All Maps" table (first one)
                    if i == 0 and ("All Maps" in table_context or table_context == ""):
                        if map_name == "All Maps":
                            economy_table = table
                            print(f"ECONOMY: Using 'All Maps' table for {map_name}")
                            break
                        continue

                    # For individual map tables, match by map name
                    if map_name.lower() in table_context.lower():
                        economy_table = table
                        print(f"ECONOMY: Found matching table for {map_name} in context: {table_context}")
                        break

                # Fallback: if we couldn't match by context, use positional logic
                if not economy_table and len(economy_tables_found) > 1:
                    # Map the map names to table positions (after "All Maps")
                    map_order = ["Abyss", "Bind", "Lotus"]  # Based on the observed order
                    try:
                        map_index = map_order.index(map_name)
                        table_index = map_index + 1  # +1 because first table is "All Maps"
                        if table_index < len(economy_tables_found):
                            economy_table = economy_tables_found[table_index]
                            print(f"ECONOMY: Using fallback position {table_index} for {map_name}")
                    except ValueError:
                        print(f"WARNING: Unknown map name: {map_name}")

                # Final fallback
                if not economy_table and len(economy_tables_found) >= 2:
                    economy_table = economy_tables_found[1]  # Default to second table
                    print(f"WARNING: Using default second table for {map_name}")

            if not economy_table:
                print(f"WARNING: No economy table found for {map_name}")
                return []

            # Extract data from the selected economy table
            rows = economy_table.find_all('tr')[1:]  # Skip header row
            headers = economy_table.find_all('th')
            header_texts = [th.get_text(strip=True) for th in headers]

            for row in rows:
                cells = row.find_all('td')

                # Skip rows without enough cells
                if len(cells) < 2:
                    continue

                # Extract team name from first cell
                team_name = cells[0].get_text(strip=True)
                if not team_name:
                    continue

                # Initialize team data
                team_data = {
                    'map': map_name,
                    'team': team_name,
                    'pistol_won': 'N/A',
                    'eco_won': 'N/A',
                    'semi_eco_won': 'N/A',
                    'semi_buy_won': 'N/A',
                    'full_buy_won': 'N/A'
                }

                # Extract economy metrics based on header positions
                for i, header in enumerate(header_texts):
                    if i < len(cells):
                        cell_text = cells[i].get_text(strip=True)
                        # Clean up the text by removing extra whitespace and extracting just the number
                        cell_text = self._clean_economy_text(cell_text)

                        if header == 'Pistol Won':
                            team_data['pistol_won'] = cell_text
                        elif header == 'Eco (won)' or header == 'Eco':
                            team_data['eco_won'] = cell_text
                        elif header == '$ (won)' or header == '$':
                            team_data['semi_eco_won'] = cell_text
                        elif header == '$$ (won)' or header == '$$':
                            team_data['semi_buy_won'] = cell_text
                        elif header == '$$$ (won)' or header == '$$$':
                            team_data['full_buy_won'] = cell_text

                team_economy_data.append(team_data)
                print(f"📊 Extracted economy data for {team_name}: {team_data}")

            return team_economy_data

        except Exception as e:
            print(f"WARNING: Error extracting team economy data: {e}")
            return []

    def _get_table_context(self, table, soup):
        """
        Get context around a table to identify which map it belongs to

        Args:
            table: BeautifulSoup table element
            soup: Full page soup

        Returns:
            str: Context string that might contain map name
        """
        try:
            context_text = ""

            # Look for map navigation or headers before this table
            # Check previous siblings for map indicators
            current = table
            for _ in range(10):  # Look up to 10 elements back
                current = current.find_previous_sibling()
                if not current:
                    break

                text = current.get_text(strip=True)
                if text and any(map_name in text for map_name in ["All Maps", "Abyss", "Bind", "Lotus", "Haven", "Ascent", "Icebox", "Breeze", "Fracture", "Pearl", "Split", "Sunset"]):
                    context_text = text
                    break

            # Also check for map tabs or navigation elements
            if not context_text:
                # Look for map navigation elements
                map_tabs = soup.find_all(['div', 'span', 'a'], string=lambda text: text and any(map_name in text for map_name in ["All Maps", "Abyss", "Bind", "Lotus", "Haven", "Ascent", "Icebox", "Breeze", "Fracture", "Pearl", "Split", "Sunset"]))
                if map_tabs:
                    # Find the closest map tab to our table
                    for tab in map_tabs:
                        tab_text = tab.get_text(strip=True)
                        if tab_text:
                            context_text = tab_text
                            break

            return context_text

        except Exception as e:
            print(f"WARNING: Error getting table context: {e}")
            return ""

    def _extract_team_economy_data_from_table(self, table, map_name):
        """
        Extract team economy data directly from a specific table

        Args:
            table: BeautifulSoup table element
            map_name (str): Name of the map this table represents

        Returns:
            list: List of team economy data dictionaries
        """
        try:
            team_economy_data = []

            # Find all rows in the table
            rows = table.find_all('tr')

            if len(rows) < 2:  # Need at least header + 1 data row
                print(f"WARNING: Not enough rows in economy table for {map_name}")
                return []

            # Process each data row (skip header row)
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])

                if len(cells) < 6:  # Need at least 6 columns
                    continue

                # Extract team name from first cell
                team_cell = cells[0]
                team_name = team_cell.get_text(strip=True)

                if not team_name:
                    continue

                # Extract economy data from subsequent cells
                pistol_won = self._clean_economy_text(cells[1].get_text(strip=True))
                eco_won = self._clean_economy_text(cells[2].get_text(strip=True))
                semi_eco_won = self._clean_economy_text(cells[3].get_text(strip=True))
                semi_buy_won = self._clean_economy_text(cells[4].get_text(strip=True))
                full_buy_won = self._clean_economy_text(cells[5].get_text(strip=True))

                team_data = {
                    'map': map_name,
                    'Team': team_name,
                    'Pistol Won': pistol_won,
                    'Eco (won)': eco_won,
                    'Semi-eco (won)': semi_eco_won,
                    'Semi-buy (won)': semi_buy_won,
                    'Full buy(won)': full_buy_won
                }

                team_economy_data.append(team_data)

            return team_economy_data

        except Exception as e:
            print(f"WARNING: Error extracting team economy data from table for {map_name}: {e}")
            return []

    def _clean_economy_text(self, text):
        """Clean economy text by extracting the main number and won count"""
        try:
            if not text:
                return 'N/A'

            # Remove extra whitespace and tabs
            text = re.sub(r'\s+', ' ', text.strip())

            # Extract the pattern like "10 (3)" where 10 is total and 3 is won
            # We want to keep the format "10 (3)" but clean it up
            match = re.search(r'(\d+)\s*\(\s*(\d+)\s*\)', text)
            if match:
                total = match.group(1)
                won = match.group(2)
                return f"{total} ({won})"

            # If no parentheses pattern, just return the first number found
            number_match = re.search(r'\d+', text)
            if number_match:
                return number_match.group(0)

            return text.strip()
        except:
            return 'N/A'

    def _safe_extract_number(self, cell):
        """Safely extract number from table cell"""
        try:
            text = cell.get_text(strip=True)
            # Remove currency symbols and commas
            text = re.sub(r'[,$]', '', text)
            # Handle percentage values
            if '%' in text:
                return text
            # Handle numeric values
            if text.replace('.', '').isdigit():
                return float(text) if '.' in text else int(text)
            return text if text else 0
        except:
            return 0

    def save_economy_data(self, economy_data, filename=None):
        """Save economy data to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"match_economy_data_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(economy_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Economy data saved to: {filename}")
            return filename

        except Exception as e:
            print(f"ERROR: Error saving economy data: {e}")
            return None

def main():
    """Test the economy scraper"""
    scraper = DetailedMatchEconomyScraper()

    # Test URL - using the GEN vs SEN match that the user mentioned
    test_url = "https://www.vlr.gg/378662/geng-vs-sentinels-valorant-champions-2024-opening-a/"

    print("ECONOMY: VLR Detailed Match Economy Scraper")
    print("=" * 60)

    # Scrape economy data
    economy_data = scraper.get_match_economy_data(test_url)

    if economy_data:
        print(f"\n✅ Successfully scraped economy data!")
        print(f"📊 Match ID: {economy_data.get('match_id', 'N/A')}")
        print(f"🗺️ Economy records found: {len(economy_data.get('economy_data', []))}")

        # Save data
        scraper.save_economy_data(economy_data)

        # Display sample data
        print(f"\n📋 Sample Economy Data:")
        for i, team_data in enumerate(economy_data.get('economy_data', [])):
            print(f"  {i+1}. Map: {team_data.get('map', 'N/A')}")
            print(f"     Team: {team_data.get('team', 'N/A')}")
            print(f"     Pistol Won: {team_data.get('pistol_won', 'N/A')}")
            print(f"     Eco Won: {team_data.get('eco_won', 'N/A')}")
            print(f"     Semi-eco Won: {team_data.get('semi_eco_won', 'N/A')}")
            print(f"     Semi-buy Won: {team_data.get('semi_buy_won', 'N/A')}")
            print(f"     Full-buy Won: {team_data.get('full_buy_won', 'N/A')}")
            print()

        print(f"\nSUCCESS: Economy scraping complete!")

    else:
        print(f"\nERROR: Failed to scrape economy data")

if __name__ == "__main__":
    main()
