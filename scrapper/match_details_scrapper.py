import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import time
import re
import json
from datetime import datetime
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
# Optional: from webdriver_manager.chrome import ChromeDriverManager

class MatchDetailsScraper:
    def __init__(self):
        self.base_url = "https://www.vlr.gg"
        # Selenium setup
        self.chrome_options = ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--window-size=1920,1080")
        # Ensure chromedriver is in PATH or use webdriver_manager:
        # self.driver_service = ChromeService(ChromeDriverManager().install())
        try:
            self.driver_service = ChromeService() # Assumes chromedriver is in PATH
        except Exception as e:
            print(f"Error initializing ChromeService. Ensure ChromeDriver is in your PATH or installed via webdriver-manager: {e}")
            self.driver_service = None # Allow script to run if only using pre-fetched HTML
        self.driver = None

    def _init_driver(self):
        if not self.driver_service:
            raise Exception("ChromeDriver service not initialized. Cannot start Selenium.")
        if not self.driver or not self.driver.service.is_connectable():
            try:
                self.driver = webdriver.Chrome(service=self.driver_service, options=self.chrome_options)
            except Exception as e:
                print(f"Error starting WebDriver: {e}")
                self.driver = None
                raise

    def _quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error quitting WebDriver: {e}")
            self.driver = None

    def _safe_get_text(self, element: Optional[BeautifulSoup], default: str = 'N/A') -> str:
        """Safely get text from a BeautifulSoup element."""
        if element:
            text = element.get_text(strip=True)
            return text if text else default # Return default if stripped text is empty
        return default

    def _extract_match_id(self, url: str) -> Optional[str]:
        """Extract the numeric match ID from a VLR.gg match URL."""
        match = re.search(r'/(\d+)/', url)
        return match.group(1) if match else None

    def _parse_player_row_stats(self, row_soup: BeautifulSoup, team_name: str) -> Dict[str, Any]:
        """Parses a single player's stats from a table row."""
        player_data = {}
        player_data['team_name'] = team_name
        cells = row_soup.find_all('td')

        # Player Name and ID from the first cell
        player_cell = cells[0]
        player_name_tag = player_cell.find('a') # This is the anchor tag for the player

        player_data['player_id'] = None
        if player_name_tag and player_name_tag.has_attr('href'):
            player_url = player_name_tag['href']
            id_match = re.search(r'/player/(\d+)/', player_url)
            if id_match:
                player_data['player_id'] = id_match.group(1)

        player_div_text_of = player_name_tag.find('div', class_='text-of') if player_name_tag else None
        # Prioritize text from 'div.text-of', then 'a' tag, then the whole cell
        player_data['player_name'] = self._safe_get_text(player_div_text_of, 
                                                        self._safe_get_text(player_name_tag, 
                                                                            default=self._safe_get_text(player_cell, default="N/A")))


        # Agent parsing - both overview and per-map styles have agent in cells[1]
        agent_cell = cells[1] if len(cells) > 1 else None
        player_data['agent'] = 'N/A'
        player_data['agents'] = []

        if agent_cell:
            # Look for agent spans with mod-agent class
            agent_spans = agent_cell.find_all('span', class_=lambda c: c and 'mod-agent' in c.split())
            agent_imgs = []

            for span_tag in agent_spans:
                img = span_tag.find('img')
                if img:
                    agent_imgs.append(img)

            # Extract agent names from images
            agent_names = []
            for img in agent_imgs:
                # Prioritize 'alt' text for agent name, fallback to 'title'
                agent_name = img.get('alt', '').strip()
                if not agent_name:
                    agent_name = img.get('title', '').strip()

                # If alt/title failed, try to derive from src
                if not agent_name:
                    img_src = img.get('src', '')
                    if '/img/vlr/game/agents/' in img_src:
                        # Extract from src: e.g. /img/vlr/game/agents/kill-joy.png -> Killjoy
                        extracted_from_src = img_src.split('/agents/')[-1].split('.')[0].replace('-', '')
                        if extracted_from_src and len(extracted_from_src) < 20:
                            agent_name = extracted_from_src.title()

                # Validate and add agent name
                if agent_name and 0 < len(agent_name) < 20 and not any(c in agent_name for c in ['/', '.']):
                    agent_names.append(agent_name.title())

            player_data['agents'] = agent_names
            player_data['agent'] = agent_names[0] if agent_names else 'N/A'


        # Correct stat column order based on HTML analysis: Rating, ACS, K, D, A, K/D Diff, KAST, ADR, HS%, FK, FD, FK/FD Diff
        stat_keys = ['rating', 'acs', 'k', 'd', 'a', 'kd_diff', 'kast', 'adr', 'hs_percent', 'fk', 'fd', 'fk_fd_diff']
        # Both overview and per-map styles have: Player Name in cells[0], Agent in cells[1], Stats start at cells[2]
        stat_start_index = 2

        player_data['stats_all_sides'] = {}
        player_data['stats_attack'] = {}
        player_data['stats_defense'] = {}

        for i, key_name in enumerate(stat_keys):
            cell_index = stat_start_index + i
            if cell_index < len(cells):
                stat_cell = cells[cell_index]
                
                # --- Extracting 'stats_all_sides' ---
                stat_value_all_sides = "N/A"
                # Primary target for the 'all sides' value (e.g. Rating, ACS)
                target_span_both_specific = stat_cell.find('span', class_='side mod-side mod-both') # Found in Rating, ACS, etc.
                if target_span_both_specific:
                    stat_value_all_sides = self._safe_get_text(target_span_both_specific)

                if stat_value_all_sides == "N/A" or stat_value_all_sides == "": # Fallback 1
                    target_span_both_general = stat_cell.find('span', class_='mod-both')
                    if target_span_both_general:
                        stat_value_all_sides = self._safe_get_text(target_span_both_general)
                
                if stat_value_all_sides == "N/A" or stat_value_all_sides == "": # Fallback 2
                    stats_sq_span = stat_cell.find('span', class_='stats-sq')
                    # Check if the stats-sq span itself holds the value, not just T/CT sides
                    if stats_sq_span:
                        if not (stats_sq_span.find('span', class_='mod-t') or stats_sq_span.find('span', class_='mod-ct')):
                            potential_value_text = self._safe_get_text(stats_sq_span)
                            # Ensure this text is not just a container for T/CT values if they exist at cell level
                            if potential_value_text and potential_value_text not in [
                                self._safe_get_text(stat_cell.find('span', class_='mod-t')),
                                self._safe_get_text(stat_cell.find('span', class_='mod-ct'))
                            ]:
                                stat_value_all_sides = potential_value_text
                
                if stat_value_all_sides == "N/A" or stat_value_all_sides == "": # Final fallback: direct text of the cell
                    if not (stat_cell.find('span', class_='mod-t') or stat_cell.find('span', class_='mod-ct')):
                        direct_cell_text = self._safe_get_text(stat_cell)
                        if direct_cell_text != "N/A" and direct_cell_text != "": # Ensure it's not empty
                            stat_value_all_sides = direct_cell_text
                
                player_data['stats_all_sides'][key_name] = "N/A" if stat_value_all_sides == "" or stat_value_all_sides.isspace() else stat_value_all_sides.strip()

                # --- Extracting 'stats_attack' ---
                stat_value_attack = "N/A"
                target_span_t = stat_cell.find('span', class_='side mod-side mod-t')
                if not target_span_t: target_span_t = stat_cell.find('span', class_='mod-t') # Fallback
                if target_span_t: stat_value_attack = self._safe_get_text(target_span_t)
                player_data['stats_attack'][key_name] = "N/A" if stat_value_attack == "" or stat_value_attack.isspace() else stat_value_attack.strip()

                # --- Extracting 'stats_defense' ---
                stat_value_defense = "N/A"
                target_span_ct = stat_cell.find('span', class_='side mod-side mod-ct')
                if not target_span_ct: target_span_ct = stat_cell.find('span', class_='mod-ct') # Fallback
                if target_span_ct: stat_value_defense = self._safe_get_text(target_span_ct)
                player_data['stats_defense'][key_name] = "N/A" if stat_value_defense == "" or stat_value_defense.isspace() else stat_value_defense.strip()
            else:
                player_data['stats_all_sides'][key_name] = 'N/A'
                player_data['stats_attack'][key_name] = 'N/A'
                player_data['stats_defense'][key_name] = 'N/A'
        return player_data

    def _parse_player_stats_table(self, table_soup: BeautifulSoup, team_name: str) -> List[Dict[str, Any]]:
        """Parses a full player stats table (e.g., for one team on one map)."""
        player_stats_list = []
        stat_rows = table_soup.find('tbody').find_all('tr') if table_soup.find('tbody') else []
        for row_soup in stat_rows:
            player_stats_list.append(self._parse_player_row_stats(row_soup, team_name))
        return player_stats_list

    def _extract_match_header_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extracts information from the main match header.
        """
        header_info = {
            'event_name': 'N/A', 'event_stage': 'N/A', 'match_date_utc': 'N/A',
            'patch': 'N/A', 'team1_name': 'N/A', 'team2_name': 'N/A',
            'team1_score_overall': 0, 'team2_score_overall': 0,
            'match_format': 'N/A', 'map_picks_bans_note': 'N/A'
        }
        match_header_super = soup.find('div', class_='match-header-super')
        if match_header_super:
            event_link_tag = match_header_super.find('a', class_='match-header-event')
            if event_link_tag:
                event_divs = event_link_tag.find_all('div', recursive=False)
                if len(event_divs) > 0 and event_divs[0].find('div'): 
                     header_info['event_name'] = self._safe_get_text(event_divs[0].find_all('div')[0])
                     if len(event_divs[0].find_all('div')) > 1:
                        header_info['event_stage'] = self._safe_get_text(event_divs[0].find_all('div')[1])

            date_container = match_header_super.find('div', class_='match-header-date')
            if date_container:
                moment_tag = date_container.find('div', class_='moment-tz-convert')
                if moment_tag and moment_tag.has_attr('data-utc-ts'):
                    header_info['match_date_utc'] = moment_tag['data-utc-ts']
                patch_tag = date_container.find('div', style=lambda x: x and 'italic' in x)
                header_info['patch'] = self._safe_get_text(patch_tag)

        match_header_vs = soup.find('div', class_='match-header-vs')
        if match_header_vs:
            team1_tag = match_header_vs.find('a', class_='match-header-link mod-1')
            if team1_tag:
                 header_info['team1_name'] = self._safe_get_text(team1_tag.find('div', class_='wf-title-med'))

            team2_tag = match_header_vs.find('a', class_='match-header-link mod-2')
            if team2_tag:
                header_info['team2_name'] = self._safe_get_text(team2_tag.find('div', class_='wf-title-med'))

            score_container = match_header_vs.find('div', class_='match-header-vs-score')
            if score_container:
                score_spoiler = score_container.find('div', class_='js-spoiler')
                if score_spoiler:
                    scores = score_spoiler.find_all('span')
                    if len(scores) == 3: 
                        try:
                            s1 = int(self._safe_get_text(scores[0], '0'))
                            s2 = int(self._safe_get_text(scores[2], '0'))
                            # The scores s1 and s2 are directly from the spans.
                            # The winner class indicates who won, but s1 is always from scores[0]
                            # and s2 from scores[2] based on typical HTML order.
                            header_info['team1_score_overall'] = s1
                            header_info['team2_score_overall'] = s2
                        except ValueError:
                            pass 
                
                format_tag_elements = score_container.find_all('div', class_='match-header-vs-note')
                if len(format_tag_elements) > 1 : 
                    header_info['match_format'] = self._safe_get_text(format_tag_elements[1])
                elif len(format_tag_elements) == 1 and "final" not in self._safe_get_text(format_tag_elements[0]).lower():
                    header_info['match_format'] = self._safe_get_text(format_tag_elements[0])

        map_note_tag = soup.find('div', class_='match-header-note') 
        header_info['map_picks_bans_note'] = self._safe_get_text(map_note_tag)
        return header_info

    def _extract_maps_data(self, soup: BeautifulSoup, team1_name_overall: str, team2_name_overall: str) -> List[Dict[str, Any]]:
        """Extracts data for each map played."""
        maps_data_list = []
        # Selects map sections, excluding the "All Maps" overview
        map_sections = soup.select('div.vm-stats-container > div.vm-stats-game[data-game-id]:not([data-game-id="all"])')

        for i, map_section_soup in enumerate(map_sections):
            map_id_attr = map_section_soup.get('data-game-id', f"map_{i+1}_unknown_id")
            map_data = {
                'map_order': i + 1,
                'map_id': map_id_attr, # Add the extracted map_id
                'player_stats': {team1_name_overall: [], team2_name_overall: []}
            }
            
            header = map_section_soup.find('div', class_='vm-stats-game-header')
            if not header: continue

            map_info_div = header.find('div', class_='map')
            if not map_info_div: continue

            map_name_container = map_info_div.find('div', style=lambda x: x and 'font-weight: 700' in x)
            map_name_span = map_name_container.find('span') if map_name_container else None
            map_data['map_name'] = self._safe_get_text(map_name_span).replace('PICK', '').strip()
            map_data['map_duration'] = self._safe_get_text(map_info_div.find('div', class_='map-duration'))
            
            if map_name_span:
                picked_by_span = map_name_span.find('span', class_=lambda x: x and 'picked' in x)
                if picked_by_span:
                    # mod-1 usually corresponds to team1, mod-2 to team2 in VLR's structure
                    if 'mod-1' in picked_by_span.get('class', []): 
                        map_data['picked_by'] = team1_name_overall
                    elif 'mod-2' in picked_by_span.get('class', []):
                        map_data['picked_by'] = team2_name_overall
                    else: # If no mod-1 or mod-2, it might be a decider or unpicked
                        map_data['picked_by'] = "Decider" 
                else: # If no 'picked' span, assume decider or not specified
                     map_data['picked_by'] = "Decider" # Or "N/A" if preferred
            else:
                map_data['picked_by'] = "N/A"


            scores = header.find_all('div', class_='score')
            if len(scores) >= 2:
                map_data['team1_score_map'] = int(self._safe_get_text(scores[0], '0'))
                map_data['team2_score_map'] = int(self._safe_get_text(scores[1], '0'))

                if map_data['team1_score_map'] > map_data['team2_score_map']:
                    map_data['winner_team_name'] = team1_name_overall
                elif map_data['team2_score_map'] > map_data['team1_score_map']:
                    map_data['winner_team_name'] = team2_name_overall
                else:
                    map_data['winner_team_name'] = "Draw"
            else:
                map_data['team1_score_map'] = 0
                map_data['team2_score_map'] = 0
                map_data['winner_team_name'] = "N/A"

            # Player stats tables for this map
            player_stat_tables = map_section_soup.select('div > table.wf-table-inset.mod-overview')
            # Assuming the first table is for team1 and the second for team2 as per VLR structure
            if len(player_stat_tables) >= 1:
                 map_data['player_stats'][team1_name_overall] = self._parse_player_stats_table(player_stat_tables[0], team_name=team1_name_overall)
            if len(player_stat_tables) >= 2:
                 map_data['player_stats'][team2_name_overall] = self._parse_player_stats_table(player_stat_tables[1], team_name=team2_name_overall)

            maps_data_list.append(map_data)
        return maps_data_list

    def _extract_overall_player_stats(self, soup: BeautifulSoup, team1_name_overall: str, team2_name_overall: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts player stats from the 'All Maps' overview section."""
        overall_stats = {team1_name_overall: [], team2_name_overall: []}
        all_maps_section = soup.find('div', class_='vm-stats-game', attrs={'data-game-id': 'all'})
        if all_maps_section:
            player_stat_tables = all_maps_section.select('div > table.wf-table-inset.mod-overview')
            if len(player_stat_tables) >= 1:
                overall_stats[team1_name_overall] = self._parse_player_stats_table(player_stat_tables[0], team_name=team1_name_overall)
            if len(player_stat_tables) >= 2:
                overall_stats[team2_name_overall] = self._parse_player_stats_table(player_stat_tables[1], team_name=team2_name_overall)
        return overall_stats

    def get_match_details(self, match_url: str, html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape detailed match information from a VLR.gg match URL or provided HTML.
        """
        soup = None
        try:
            if html_content:
                print("Parsing provided HTML content.")
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                print(f"Fetching HTML using Selenium from URL: {match_url}")
                self._init_driver()
                if not self.driver:
                    print("Selenium WebDriver could not be initialized. Aborting.")
                    return {}
                
                self.driver.get(match_url)
                try:
                    # Wait for a key element that indicates player stats tables are loaded
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table.wf-table-inset.mod-overview"))
                    )
                    print("Key stats tables loaded.")
                except TimeoutException:
                    print("Warning: Page timed out waiting for key stats tables. Proceeding with current page source.")
                
                time.sleep(2) # Allow some grace time for any final JS rendering
                
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                print("HTML fetched successfully using Selenium.")

            if not soup:
                print("Error: BeautifulSoup object is None. Cannot parse HTML.")
                return {}

            header_info = self._extract_match_header_info(soup)
            team1_name = header_info.get('team1_name', 'Team 1')
            team2_name = header_info.get('team2_name', 'Team 2')
            
            # Fallback for team names if header parsing fails or returns defaults
            if team1_name == 'Team 1' or team1_name == 'N/A' or team2_name == 'Team 2' or team2_name == 'N/A':
                team_name_elements = soup.select('div.match-header-link-name .wf-title-med') # More specific selector
                if len(team_name_elements) > 0: team1_name = self._safe_get_text(team_name_elements[0], team1_name)
                if len(team_name_elements) > 1: team2_name = self._safe_get_text(team_name_elements[1], team2_name)


            match_data = {
                'match_url': match_url,
                'match_id': self._extract_match_id(match_url),
                'scraped_at': datetime.now().isoformat(),
                'event_info': {
                    'name': header_info['event_name'],
                    'stage': header_info['event_stage'],
                    'date_utc': header_info['match_date_utc'],
                    'patch': header_info['patch']
                },
                'teams': {
                    'team1': {'name': team1_name, 'score_overall': header_info['team1_score_overall']},
                    'team2': {'name': team2_name, 'score_overall': header_info['team2_score_overall']}
                },
                'match_format': header_info['match_format'],
                'map_picks_bans_note': header_info['map_picks_bans_note'],
                'maps': self._extract_maps_data(soup, team1_name, team2_name),
                'overall_player_stats': self._extract_overall_player_stats(soup, team1_name, team2_name)
            }
            
            return match_data

        except Exception as e:
            print(f"Error scraping match details for {match_url}: {str(e)}")
            traceback.print_exc()
            return {}
        finally:
            if not html_content: # Only quit driver if it was initialized by this method
                self._quit_driver()

    def create_match_dataframe(self, match_data: Dict) -> pd.DataFrame:
        """Convert match data to pandas DataFrame, including "All Maps" stats."""
        all_player_stats_list = []
        
        # Process per-map player stats
        for map_info in match_data.get('maps', []):
            map_name = map_info.get('map_name', 'N/A')
            map_id_for_row = map_info.get('map_id') 
            for team_name_key, players_list in map_info.get('player_stats', {}).items():
                for player_stat in players_list:
                    flat_stat = {
                        'match_id': match_data.get('match_id'),
                        'event_name': match_data.get('event_info', {}).get('name'),
                        'map_id': map_id_for_row,
                        'team1_overall': match_data.get('teams',{}).get('team1',{}).get('name'),
                        'team2_overall': match_data.get('teams',{}).get('team2',{}).get('name'),
                        'map_name': map_name,
                        'player_team_name': player_stat.get('team_name'),
                        'player_name': player_stat.get('player_name'),
                        'player_id': player_stat.get('player_id'),
                        'agent': player_stat.get('agent'),
                    }
                    flat_stat.update({f"{k}_all_sides": v for k, v in player_stat.get('stats_all_sides', {}).items()})
                    flat_stat.update({f"{k}_attack": v for k, v in player_stat.get('stats_attack', {}).items()})
                    flat_stat.update({f"{k}_defense": v for k, v in player_stat.get('stats_defense', {}).items()})
                    all_player_stats_list.append(flat_stat)
        
        # Process "All Maps" (overall) player stats
        overall_stats_data = match_data.get('overall_player_stats', {})
        for team_name_key, players_list in overall_stats_data.items():
            for player_stat in players_list:
                flat_stat = {
                    'match_id': match_data.get('match_id'),
                    'event_name': match_data.get('event_info', {}).get('name'),
                    'map_id': "all", # Special map_id for overall stats
                    'team1_overall': match_data.get('teams',{}).get('team1',{}).get('name'),
                    'team2_overall': match_data.get('teams',{}).get('team2',{}).get('name'),
                    'map_name': "All Maps", # Special map_name for overall stats
                    'player_team_name': player_stat.get('team_name'),
                    'player_name': player_stat.get('player_name'),
                    'player_id': player_stat.get('player_id'),
                    'agent': player_stat.get('agent'), # Primary agent for overall
                }
                flat_stat.update({f"{k}_all_sides": v for k, v in player_stat.get('stats_all_sides', {}).items()})
                flat_stat.update({f"{k}_attack": v for k, v in player_stat.get('stats_attack', {}).items()})
                flat_stat.update({f"{k}_defense": v for k, v in player_stat.get('stats_defense', {}).items()})
                all_player_stats_list.append(flat_stat)

        if not all_player_stats_list:
            return pd.DataFrame() 
            
        return pd.DataFrame(all_player_stats_list)

def main():
    scraper = MatchDetailsScraper()
    match_url = "https://www.vlr.gg/371266/kr-esports-vs-cloud9-champions-tour-2024-americas-stage-2-ko"

    print(f"Attempting to scrape match details from: {match_url}")

    # Option 1: Scrape from the live URL (using Selenium)
    match_data = scraper.get_match_details(match_url)

    # Option 2: Load from pre-saved HTML file (for testing parsing logic without hitting network/Selenium)
    # html_file_path = r"vlr_kru_vs_cloud9.html"
    # print(f"Attempting to load HTML from: {html_file_path}")
    # try:
    #     with open(html_file_path, 'r', encoding='utf-8') as f:
    #         html_content_for_test = f.read()
    #     match_data = scraper.get_match_details(match_url, html_content=html_content_for_test)
    # except FileNotFoundError:
    #     print(f"Error: HTML file not found at {html_file_path}.")
    #     match_data = {}
    # except Exception as e:
    #     print(f"Error loading HTML file: {e}")
    #     match_data = {}

    if match_data:
        print("\n--- Scraped Match Data (JSON) ---")
        print(json.dumps(match_data, indent=2, ensure_ascii=False))
        
        output_filename_json = "detailed_match_data.json"
        try:
            with open(output_filename_json, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Detailed match data successfully saved to {output_filename_json}")
        except IOError as e:
            print(f"\n❌ Error saving JSON data to {output_filename_json}: {e}")

        # Create and save DataFrame
        df = scraper.create_match_dataframe(match_data)
        if not df.empty:
            print("\n--- Scraped Match Data (DataFrame Sample) ---")
            print(df.head().to_string())
            output_filename_csv = "detailed_match_data.csv"
            try:
                df.to_csv(output_filename_csv, index=False, encoding='utf-8-sig')
                print(f"\n✅ Detailed match data successfully saved to {output_filename_csv}")
            except IOError as e:
                print(f"\n❌ Error saving CSV data to {output_filename_csv}: {e}")
        else:
            print("\nℹ️ No player-map statistics found to create a DataFrame.")
            
    else:
        print("\n❌ Failed to scrape match details or no data was returned.")

if __name__ == "__main__":
    main()
