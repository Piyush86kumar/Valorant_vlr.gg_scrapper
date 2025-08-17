import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

class MatchesScraper:
    """
    Dedicated scraper for VLR.gg matches data
    Handles match details, scores, series information, and team performance
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def construct_matches_url(self, main_url: str) -> str:
        """
        Construct matches URL from main event URL
        Example: https://www.vlr.gg/event/2097/valorant-champions-2024
        -> https://www.vlr.gg/event/matches/2097/valorant-champions-2024
        """
        try:
            # Extract event ID
            match = re.search(r'/event/(\d+)/', main_url)
            if not match:
                raise ValueError("Could not extract event ID from URL")

            event_id = match.group(1)

            # Extract event name from URL
            url_parts = main_url.split('/')
            event_name = url_parts[-1] if url_parts[-1] else url_parts[-2]

            matches_url = f"https://www.vlr.gg/event/matches/{event_id}/{event_name}"
            return matches_url

        except Exception as e:
            raise ValueError(f"Error constructing matches URL: {e}")

    def scrape_matches(self, main_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Scrape all matches data from the matches tab
        """
        try:
            matches_url = self.construct_matches_url(main_url)

            if progress_callback:
                progress_callback("Fetching matches page...")

            response = self.session.get(matches_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            if progress_callback:
                progress_callback("Parsing matches data...")

            # Extract matches
            matches = self._extract_matches(soup, progress_callback)

            # Extract series information
            series_info = self._extract_series_info(soup)

            # Extract tournament bracket info if available
            bracket_info = self._extract_bracket_info(soup)

            result = {
                'matches': matches,
                'series_info': series_info,
                'bracket_info': bracket_info,
                'total_matches': len(matches),
                'scraped_from': matches_url,
                'scraped_at': datetime.now().isoformat()
            }

            if progress_callback:
                progress_callback(f"Completed! Found {len(matches)} matches")

            return result

        except Exception as e:
            raise Exception(f"Error scraping matches: {e}")

    def _extract_matches(self, soup: BeautifulSoup, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract individual match data using correct VLR.gg selectors"""
        matches = []

        # Find all match day containers using correct VLR.gg structure
        match_days = soup.select("div.vm-date")

        if not match_days:
            if progress_callback:
                progress_callback("Using VLR.gg match-item structure...")

            # Use the actual VLR.gg structure with date labels and match items
            matches = self._extract_matches_with_date_labels(soup, progress_callback)

        else:
            # Use the vm-date structure (if found)
            total_matches = sum(len(day.find_all('a', class_='vm-match')) for day in match_days)
            processed = 0

            for day in match_days:
                # Extract date for this day
                date_label = day.find('div', class_='vm-date-label')
                match_date = date_label.get_text(strip=True) if date_label else 'N/A'

                # Find all matches for this day
                match_rows = day.find_all('a', class_='vm-match')

                for row in match_rows:
                    processed += 1
                    if progress_callback and processed % 5 == 0:
                        progress_callback(f"Processing match {processed}/{total_matches}")

                    match_data = self._extract_single_match_vlr(row, match_date)
                    if match_data:
                        matches.append(match_data)

                    # Small delay to be respectful
                    time.sleep(0.1)

        return matches

    def _extract_matches_with_date_labels(self, soup: BeautifulSoup, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract matches using the wf-label date structure"""
        matches = []

        # Find all elements that could be date labels or match containers
        all_elements = soup.find_all(['div', 'a'])

        current_date = "N/A"
        match_containers = []

        # First pass: collect all match containers and associate them with dates
        for element in all_elements:
            # Check if this is a date label
            if element.name == 'div' and 'wf-label' in element.get('class', []) and 'mod-large' in element.get('class', []):
                current_date = element.get_text(strip=True)
                continue

            # Check if this is a match container
            if (element.name == 'a' and
                'wf-module-item' in element.get('class', []) and
                'match-item' in element.get('class', [])):
                match_containers.append((element, current_date))

        # Process all match containers
        for i, (container, match_date) in enumerate(match_containers):
            if progress_callback and i % 10 == 0:
                progress_callback(f"Processing match {i+1}/{len(match_containers)}")

            match_data = self._extract_single_match_new(container, match_date)
            if match_data:
                matches.append(match_data)

            # Small delay to be respectful
            time.sleep(0.1)

        return matches

    def _extract_match_id_from_url(self, url: str) -> Optional[str]:
        """Extract match ID from VLR.gg match URL"""
        try:
            match = re.search(r'/(\d+)/', url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def _extract_single_match_vlr(self, row, match_date: str) -> Optional[Dict[str, Any]]:
        """Extract data from a single VLR.gg match row using correct selectors"""
        try:
            match_data = {
                'scraped_at': datetime.now().isoformat(),
                'date': match_date
            }

            # Get match URL
            href = row.get('href', '')
            if href:
                match_url = f"https://www.vlr.gg{href}" if href.startswith('/') else href
                match_data['match_url'] = match_url
                # Extract match ID from URL
                match_data['match_id'] = self._extract_match_id_from_url(match_url)

            # Extract time
            time_elem = row.find('div', class_='vm-time')
            match_data['time'] = time_elem.get_text(strip=True) if time_elem else 'N/A'

            # Extract team names
            team_elems = row.select('div.vm-t')
            if len(team_elems) >= 2:
                team1_name = team_elems[0].find('div', class_='vm-t-name')
                team2_name = team_elems[1].find('div', class_='vm-t-name')
                match_data['team1'] = team1_name.get_text(strip=True) if team1_name else 'N/A'
                match_data['team2'] = team2_name.get_text(strip=True) if team2_name else 'N/A'

            # Extract score
            score_elem = row.find('div', class_='vm-score')
            score_text = score_elem.get_text(strip=True) if score_elem else 'N/A'
            match_data['score'] = score_text

            # Parse individual scores for winner determination
            score1 = score2 = None
            try:
                if score_text != 'N/A' and '-' in score_text:
                    score_parts = score_text.split('-')
                    if len(score_parts) == 2:
                        score1, score2 = int(score_parts[0].strip()), int(score_parts[1].strip())
                        match_data['score1'] = str(score1)
                        match_data['score2'] = str(score2)
            except (ValueError, IndexError):
                pass

            # Extract status
            status_elem = row.find('div', class_='vm-status')
            status_text = status_elem.get_text(strip=True) if status_elem else 'N/A'
            match_data['status'] = 'Completed' if score1 is not None and score2 is not None else status_text

            # Extract week and stage information
            week_elem = row.find('div', class_='vm-stats-container')
            if week_elem:
                week_text = week_elem.get_text(strip=True)

                # Extract week number
                if "Week" in week_text:
                    week_match = re.search(r'Week\s*(\d+)', week_text)
                    if week_match:
                        match_data['week'] = f"Week {week_match.group(1)}"
                    else:
                        match_data['week'] = "N/A"
                else:
                    match_data['week'] = "N/A"

                # Extract stage
                if "Regular Season" in week_text:
                    match_data['stage'] = "Regular Season"
                elif "Playoffs" in week_text:
                    match_data['stage'] = "Playoffs"
                else:
                    match_data['stage'] = "N/A"
            else:
                match_data['week'] = "N/A"
                match_data['stage'] = "N/A"

            # Determine winner
            if score1 is not None and score2 is not None:
                if score1 > score2:
                    match_data['winner'] = match_data.get('team1', '')
                elif score2 > score1:
                    match_data['winner'] = match_data.get('team2', '')
                else:
                    match_data['winner'] = "Draw"
            else:
                match_data['winner'] = "N/A"

            # Only return if we have essential data
            if match_data.get('team1') != 'N/A' and match_data.get('team2') != 'N/A':
                return match_data

            return None

        except Exception as e:
            return None

    def _extract_single_match_new(self, container, match_date: str) -> Optional[Dict[str, Any]]:
        """Extract data from a single VLR.gg match container using the correct structure"""
        try:
            match_data = {
                'scraped_at': datetime.now().isoformat(),
                'date': match_date
            }

            # Get match URL
            href = container.get('href', '')
            if href:
                match_url = f"https://www.vlr.gg{href}" if href.startswith('/') else href
                match_data['match_url'] = match_url
                # Extract match ID from URL
                match_data['match_id'] = self._extract_match_id_from_url(match_url)

            # Extract time
            time_elem = container.find('div', class_='match-item-time')
            match_data['time'] = time_elem.get_text(strip=True) if time_elem else 'N/A'

            # Extract team information
            vs_container = container.find('div', class_='match-item-vs')
            if vs_container:
                team_containers = vs_container.find_all('div', class_='match-item-vs-team')

                if len(team_containers) >= 2:
                    # Extract team 1
                    team1_name_elem = team_containers[0].find('div', class_='match-item-vs-team-name')
                    if team1_name_elem:
                        text_of_elem = team1_name_elem.find('div', class_='text-of')
                        if text_of_elem:
                            match_data['team1'] = text_of_elem.get_text(strip=True)

                    team1_score_elem = team_containers[0].find('div', class_='match-item-vs-team-score')
                    if team1_score_elem:
                        match_data['score1'] = team1_score_elem.get_text(strip=True)

                    # Extract team 2
                    team2_name_elem = team_containers[1].find('div', class_='match-item-vs-team-name')
                    if team2_name_elem:
                        text_of_elem = team2_name_elem.find('div', class_='text-of')
                        if text_of_elem:
                            match_data['team2'] = text_of_elem.get_text(strip=True)

                    team2_score_elem = team_containers[1].find('div', class_='match-item-vs-team-score')
                    if team2_score_elem:
                        match_data['score2'] = team2_score_elem.get_text(strip=True)

                    # Create combined score
                    if 'score1' in match_data and 'score2' in match_data:
                        match_data['score'] = f"{match_data['score1']}-{match_data['score2']}"

                    # Determine winner based on mod-winner class
                    winner_container = vs_container.find('div', class_='match-item-vs-team mod-winner')
                    if winner_container:
                        winner_name_elem = winner_container.find('div', class_='match-item-vs-team-name')
                        if winner_name_elem:
                            text_of_elem = winner_name_elem.find('div', class_='text-of')
                            if text_of_elem:
                                match_data['winner'] = text_of_elem.get_text(strip=True)
                    else:
                        # Fallback: determine winner by score
                        if 'score1' in match_data and 'score2' in match_data:
                            try:
                                s1, s2 = int(match_data['score1']), int(match_data['score2'])
                                if s1 > s2:
                                    match_data['winner'] = match_data.get('team1', 'N/A')
                                elif s2 > s1:
                                    match_data['winner'] = match_data.get('team2', 'N/A')
                                else:
                                    match_data['winner'] = 'Draw'
                            except (ValueError, TypeError):
                                match_data['winner'] = 'N/A'
                        else:
                            match_data['winner'] = 'N/A'

            # Extract status
            eta_container = container.find('div', class_='match-item-eta')
            if eta_container:
                status_elem = eta_container.find('div', class_='ml-status')
                match_data['status'] = status_elem.get_text(strip=True) if status_elem else 'N/A'
            else:
                match_data['status'] = 'N/A'

            # Extract week and stage information
            event_container = container.find('div', class_='match-item-event')
            if event_container:
                # Extract week
                series_elem = event_container.find('div', class_='match-item-event-series')
                if series_elem:
                    week_text = series_elem.get_text(strip=True)
                    match_data['week'] = week_text if week_text else 'N/A'
                else:
                    match_data['week'] = 'N/A'

                # Extract stage (text after the series element)
                stage_text = event_container.get_text(strip=True)
                if series_elem:
                    # Remove the week part to get the stage
                    week_text = series_elem.get_text(strip=True)
                    stage_text = stage_text.replace(week_text, '').strip()

                match_data['stage'] = stage_text if stage_text else 'N/A'
            else:
                match_data['week'] = 'N/A'
                match_data['stage'] = 'N/A'

            # Only return if we have essential data
            if match_data.get('team1') and match_data.get('team2'):
                return match_data

            return None

        except Exception as e:
            return None

    def _extract_single_match_fallback(self, container) -> Optional[Dict[str, Any]]:
        """Fallback method for extracting data from a single match container"""
        try:
            match_data = {
                'scraped_at': datetime.now().isoformat()
            }

            # Get match URL
            href = container.get('href', '')
            if href:
                match_data['match_url'] = 'https://www.vlr.gg' + href if href.startswith('/') else href

            # Extract team names
            team_elements = container.find_all(['div', 'span'], class_=re.compile(r'team.*name|match.*team'))
            if len(team_elements) >= 2:
                match_data['team1'] = team_elements[0].get_text(strip=True)
                match_data['team2'] = team_elements[1].get_text(strip=True)
            else:
                # Alternative extraction method
                team_links = container.find_all('a', href=re.compile(r'/team/'))
                if len(team_links) >= 2:
                    match_data['team1'] = team_links[0].get_text(strip=True)
                    match_data['team2'] = team_links[1].get_text(strip=True)

            # Extract scores
            score_elements = container.find_all(['div', 'span'], class_=re.compile(r'score|match.*score'))
            if len(score_elements) >= 2:
                match_data['score1'] = score_elements[0].get_text(strip=True)
                match_data['score2'] = score_elements[1].get_text(strip=True)
                match_data['score'] = f"{match_data['score1']}-{match_data['score2']}"
            else:
                # Try to find scores in text
                score_text = container.get_text()
                score_matches = re.findall(r'\b(\d+)\s*[-:]\s*(\d+)\b', score_text)
                if score_matches:
                    match_data['score1'] = score_matches[0][0]
                    match_data['score2'] = score_matches[0][1]
                    match_data['score'] = f"{match_data['score1']}-{match_data['score2']}"

            # Extract stage/round information
            stage_elements = container.find_all(['div', 'span'], class_=re.compile(r'stage|round|event'))
            if stage_elements:
                match_data['stage'] = stage_elements[0].get_text(strip=True)
            else:
                match_data['stage'] = "N/A"

            # Extract time information
            time_elements = container.find_all(['div', 'span'], class_=re.compile(r'time|date'))
            if time_elements:
                match_data['time'] = time_elements[0].get_text(strip=True)
            else:
                match_data['time'] = "N/A"

            # Set default values for missing fields
            match_data['date'] = "N/A"
            match_data['week'] = "N/A"

            # Extract series ID if available
            if href:
                series_match = re.search(r'series_id=(\d+)', href)
                if series_match:
                    match_data['series_id'] = series_match.group(1)

            # Determine match status and winner
            if 'score1' in match_data and 'score2' in match_data:
                s1, s2 = match_data['score1'], match_data['score2']
                if s1.isdigit() and s2.isdigit():
                    match_data['status'] = 'Completed'
                    s1_int, s2_int = int(s1), int(s2)
                    if s1_int > s2_int:
                        match_data['winner'] = match_data.get('team1', '')
                    elif s2_int > s1_int:
                        match_data['winner'] = match_data.get('team2', '')
                    else:
                        match_data['winner'] = 'Draw'
                else:
                    match_data['status'] = 'Scheduled'
                    match_data['winner'] = "N/A"
            else:
                match_data['status'] = 'Scheduled'
                match_data['winner'] = "N/A"

            # Only return if we have essential data
            if 'team1' in match_data and 'team2' in match_data:
                return match_data

            return None

        except Exception as e:
            return None

    def _extract_series_info(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract series information"""
        try:
            series_info = []

            # Look for series containers
            series_containers = soup.find_all(['div'], class_=re.compile(r'series|bracket'))

            for container in series_containers:
                series_data = {}

                # Extract series title
                title_elem = container.find(['h1', 'h2', 'h3', 'div'], class_=re.compile(r'title|name'))
                if title_elem:
                    series_data['title'] = title_elem.get_text(strip=True)

                # Count matches in this series
                series_matches = container.find_all('a', class_='wf-module-item')
                series_data['matches_count'] = len(series_matches)

                if series_data and series_data.get('title'):
                    series_info.append(series_data)

            return series_info

        except Exception:
            return []

    def _extract_bracket_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract tournament bracket information"""
        try:
            bracket_info = {
                'stages': [],
                'format': 'Unknown'
            }

            # Look for bracket stages
            stage_elements = soup.find_all(['div'], class_=re.compile(r'stage|round|bracket'))

            for stage_elem in stage_elements:
                stage_text = stage_elem.get_text(strip=True)
                if stage_text and len(stage_text) < 100:  # Avoid long descriptions
                    bracket_info['stages'].append(stage_text)

            # Try to determine tournament format
            page_text = soup.get_text().lower()
            if 'single elimination' in page_text:
                bracket_info['format'] = 'Single Elimination'
            elif 'double elimination' in page_text:
                bracket_info['format'] = 'Double Elimination'
            elif 'round robin' in page_text:
                bracket_info['format'] = 'Round Robin'
            elif 'swiss' in page_text:
                bracket_info['format'] = 'Swiss'

            return bracket_info

        except Exception:
            return {'stages': [], 'format': 'Unknown'}




# Example usage
if __name__ == "__main__":
    scraper = MatchesScraper()

    # Test URL
    test_url = "https://www.vlr.gg/event/2097/valorant-champions-2024"

    print("🏆 VLR Matches Scraper Test")
    print("=" * 40)

    try:
        def progress_callback(message):
            print(f"📊 {message}")

        # Scrape matches
        matches_data = scraper.scrape_matches(test_url, progress_callback)

        print(f"\n✅ Scraping completed!")
        print(f"   🏆 Total matches: {matches_data['total_matches']}")
        print(f"   📊 Series found: {len(matches_data['series_info'])}")

        # Show sample match
        if matches_data['matches']:
            sample = matches_data['matches'][0]
            print(f"   📋 Sample match: {sample.get('team1', 'N/A')} vs {sample.get('team2', 'N/A')}")
            print(f"   📊 Sample score: {sample.get('score', 'N/A')}")
            print(f"   🏆 Sample winner: {sample.get('winner', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
