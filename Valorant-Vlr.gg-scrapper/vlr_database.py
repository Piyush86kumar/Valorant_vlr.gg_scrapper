import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class VLRDatabase:  
    """
    SQLite database manager for VLR.gg scraped data
    Handles storage and retrieval of event data, matches, player stats, and agent usage
    """
    
    def __init__(self, db_path: str = "vlr_data.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
        self.migrate_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    dates TEXT,
                    location TEXT,
                    prize_pool TEXT,
                    description TEXT,
                    url TEXT,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Matches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    match_id TEXT,
                    team1 TEXT,
                    team2 TEXT,
                    score TEXT,
                    score1 TEXT,
                    score2 TEXT,
                    stage TEXT,
                    week TEXT,
                    date TEXT,
                    time TEXT,
                    match_time TEXT,
                    status TEXT,
                    winner TEXT,
                    match_url TEXT,
                    series_id TEXT,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            ''')

            # Detailed matches table for comprehensive match data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detailed_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    match_id TEXT UNIQUE,
                    match_url TEXT,
                    event_name TEXT,
                    event_stage TEXT,
                    event_date_utc TEXT,
                    patch TEXT,
                    team1_name TEXT,
                    team2_name TEXT,
                    team1_score_overall INTEGER,
                    team2_score_overall INTEGER,
                    match_format TEXT,
                    map_picks_bans_note TEXT,
                    maps_played INTEGER,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            ''')

            # Map details table for individual map data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS map_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    map_order INTEGER,
                    map_id TEXT,
                    map_name TEXT,
                    team1_score_map INTEGER,
                    team2_score_map INTEGER,
                    winner_team_name TEXT,
                    map_duration TEXT,
                    picked_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES detailed_matches (match_id)
                )
            ''')

            # Detailed player stats table for comprehensive player performance data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detailed_player_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    map_id TEXT,
                    map_name TEXT,
                    team_name TEXT,
                    player_id TEXT,
                    player_name TEXT,
                    agent TEXT,
                    agents_list TEXT,

                    -- All sides stats
                    rating_all REAL,
                    acs_all REAL,
                    kills_all INTEGER,
                    deaths_all INTEGER,
                    assists_all INTEGER,
                    kd_diff_all TEXT,
                    kast_all TEXT,
                    adr_all REAL,
                    hs_percent_all TEXT,
                    first_kills_all INTEGER,
                    first_deaths_all INTEGER,
                    fk_fd_diff_all TEXT,

                    -- Attack side stats
                    rating_attack REAL,
                    acs_attack REAL,
                    kills_attack INTEGER,
                    deaths_attack INTEGER,
                    assists_attack INTEGER,
                    kd_diff_attack TEXT,
                    kast_attack TEXT,
                    adr_attack REAL,
                    hs_percent_attack TEXT,
                    first_kills_attack INTEGER,
                    first_deaths_attack INTEGER,
                    fk_fd_diff_attack TEXT,

                    -- Defense side stats
                    rating_defense REAL,
                    acs_defense REAL,
                    kills_defense INTEGER,
                    deaths_defense INTEGER,
                    assists_defense INTEGER,
                    kd_diff_defense TEXT,
                    kast_defense TEXT,
                    adr_defense REAL,
                    hs_percent_defense TEXT,
                    first_kills_defense INTEGER,
                    first_deaths_defense INTEGER,
                    fk_fd_diff_defense TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES detailed_matches (match_id)
                )
            ''')
            
            # Player stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    player TEXT,
                    team TEXT,
                    rating REAL,
                    acs REAL,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    plus_minus INTEGER,
                    adr REAL,
                    hs_percent TEXT,
                    first_kills INTEGER,
                    first_deaths INTEGER,
                    kd_ratio REAL,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            ''')
            
            # Agent usage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    agent TEXT,
                    usage_count INTEGER,
                    usage_percentage TEXT,
                    win_rate TEXT,
                    avg_rating REAL,
                    avg_acs REAL,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_event_id ON matches (event_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_stats_event_id ON player_stats (event_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_usage_event_id ON agent_usage (event_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats (player)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_usage_agent ON agent_usage (agent)')

            # Indexes for detailed match data
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_matches_match_id ON detailed_matches (match_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_matches_event_id ON detailed_matches (event_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_map_details_match_id ON map_details (match_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_player_stats_match_id ON detailed_player_stats (match_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_player_stats_player_id ON detailed_player_stats (player_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detailed_player_stats_agent ON detailed_player_stats (agent)')
            
            conn.commit()

    def migrate_database(self):
        """Migrate existing database to new schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check current matches table schema
                cursor.execute("PRAGMA table_info(matches)")
                columns = [column[1] for column in cursor.fetchall()]

                # List of new columns to add
                new_columns = [
                    ('match_id', 'TEXT'),
                    ('score', 'TEXT'),
                    ('week', 'TEXT'),
                    ('date', 'TEXT'),
                    ('time', 'TEXT')
                ]

                migration_needed = False
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        print(f"🔄 Migrating database: Adding {col_name} column to matches table...")
                        cursor.execute(f'ALTER TABLE matches ADD COLUMN {col_name} {col_type}')
                        migration_needed = True

                if migration_needed:
                    # Update existing matches with extracted match_ids
                    cursor.execute('SELECT id, match_url FROM matches WHERE match_url IS NOT NULL AND (match_id IS NULL OR match_id = "")')
                    matches_to_update = cursor.fetchall()

                    for row_id, match_url in matches_to_update:
                        if match_url:
                            import re
                            match_id_match = re.search(r'/(\d+)/', match_url)
                            if match_id_match:
                                extracted_id = match_id_match.group(1)
                                cursor.execute('UPDATE matches SET match_id = ? WHERE id = ?', (extracted_id, row_id))

                    print("✅ Database migration completed")

                conn.commit()

        except Exception as e:
            print(f"⚠️ Database migration warning: {e}")

    def save_comprehensive_data(self, data: Dict[str, Any]) -> str:
        """
        Save comprehensive scraped data to database
        Returns the event_id for reference
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract event info and generate proper event_id
                event_info = data.get('event_info', {})
                urls = data.get('urls', {})

                # Try multiple ways to get event_id
                event_id = None
                if urls and 'event_id' in urls:
                    event_id = urls['event_id']
                elif event_info and 'url' in event_info:
                    # Extract event_id from URL
                    import re
                    url = event_info['url']
                    match = re.search(r'/event/(\d+)/', url)
                    if match:
                        event_id = match.group(1)

                # Fallback to timestamp-based ID if still unknown
                if not event_id or event_id == 'unknown':
                    event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Save event info
                cursor.execute('''
                    INSERT OR REPLACE INTO events 
                    (event_id, title, dates, location, prize_pool, description, url, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_info.get('title'),
                    event_info.get('dates'),
                    event_info.get('location'),
                    event_info.get('prize_pool'),
                    event_info.get('description'),
                    event_info.get('url'),
                    event_info.get('scraped_at')
                ))
                
                # Save matches data
                matches_data = data.get('matches_data', {})
                matches = matches_data.get('matches', [])
                
                # Clear existing matches for this event
                cursor.execute('DELETE FROM matches WHERE event_id = ?', (event_id,))
                
                for match in matches:
                    # Use the match_id that was already extracted by the scraper for reliability
                    match_id = match.get('match_id')
                    match_url = match.get('match_url', '')

                    cursor.execute('''
                        INSERT INTO matches
                        (event_id, match_id, team1, team2, score, score1, score2, stage, week,
                         date, time, match_time, status, winner, match_url, series_id, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        match_id,
                        match.get('team1'),
                        match.get('team2'),
                        match.get('score'),
                        match.get('score1'),
                        match.get('score2'),
                        match.get('stage'),
                        match.get('week'),
                        match.get('date'),
                        match.get('time'),
                        match.get('match_time'),
                        match.get('status'),
                        match.get('winner'),
                        match_url,
                        match.get('series_id'),
                        match.get('scraped_at')
                    ))
                
                # Save player stats
                stats_data = data.get('stats_data', {})
                player_stats = stats_data.get('player_stats', [])
                
                # Clear existing player stats for this event
                cursor.execute('DELETE FROM player_stats WHERE event_id = ?', (event_id,))
                
                for player in player_stats:
                    # Convert string numbers to appropriate types
                    rating = self._safe_float(player.get('rating'))
                    acs = self._safe_float(player.get('acs'))
                    kills = self._safe_int(player.get('kills'))
                    deaths = self._safe_int(player.get('deaths'))
                    assists = self._safe_int(player.get('assists'))
                    plus_minus = self._safe_int(player.get('plus_minus'))
                    adr = self._safe_float(player.get('adr'))
                    first_kills = self._safe_int(player.get('first_kills'))
                    first_deaths = self._safe_int(player.get('first_deaths'))
                    kd_ratio = self._safe_float(player.get('kd_ratio'))
                    
                    cursor.execute('''
                        INSERT INTO player_stats 
                        (event_id, player, team, rating, acs, kills, deaths, assists, 
                         plus_minus, adr, hs_percent, first_kills, first_deaths, kd_ratio, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        player.get('player'),
                        player.get('team'),
                        rating,
                        acs,
                        kills,
                        deaths,
                        assists,
                        plus_minus,
                        adr,
                        player.get('hs_percent'),
                        first_kills,
                        first_deaths,
                        kd_ratio,
                        player.get('scraped_at')
                    ))
                
                # Save agent usage data
                maps_agents_data = data.get('maps_agents_data', {})
                agents_data = maps_agents_data.get('agents', maps_agents_data.get('agent_stats', []))

                # Clear existing agent usage for this event
                cursor.execute('DELETE FROM agent_usage WHERE event_id = ?', (event_id,))

                for agent in agents_data:
                    # Handle both old and new agent data structure
                    agent_name = agent.get('agent_name', agent.get('agent', 'Unknown'))
                    usage_count = self._safe_int(agent.get('usage_count', 0))
                    usage_percentage = agent.get('total_utilization_percent', agent.get('usage_percentage', '0%'))
                    avg_rating = self._safe_float(agent.get('avg_rating'))
                    avg_acs = self._safe_float(agent.get('avg_acs'))

                    cursor.execute('''
                        INSERT INTO agent_usage
                        (event_id, agent, usage_count, usage_percentage, win_rate,
                         avg_rating, avg_acs, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        agent_name,
                        usage_count,
                        usage_percentage,
                        agent.get('win_rate'),
                        avg_rating,
                        avg_acs,
                        agent.get('scraped_at')
                    ))

                # Save detailed matches data if available
                detailed_matches = data.get('detailed_matches', [])
                if detailed_matches:
                    for match_data in detailed_matches:
                        self.save_detailed_match_data(match_data, event_id)

                conn.commit()
                return event_id

        except Exception as e:
            raise Exception(f"Error saving data to database: {e}")

    def save_detailed_match_data(self, match_data: Dict[str, Any], event_id: str = None) -> bool:
        """Save comprehensive detailed match data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Extract basic match info
                match_id = match_data.get('match_id')
                if not match_id:
                    raise ValueError("Missing required field: match_id")

                # Extract event info
                event_info = match_data.get('event_info', {})
                teams = match_data.get('teams', {})
                team1 = teams.get('team1', {})
                team2 = teams.get('team2', {})

                # Save main match record
                cursor.execute('''
                    INSERT OR REPLACE INTO detailed_matches (
                        event_id, match_id, match_url, event_name, event_stage, event_date_utc, patch,
                        team1_name, team2_name, team1_score_overall, team2_score_overall,
                        match_format, map_picks_bans_note, maps_played, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self._safe_string(event_id),
                    self._safe_string(match_id),
                    self._safe_string(match_data.get('match_url')),
                    self._safe_string(event_info.get('name')),
                    self._safe_string(event_info.get('stage')),
                    self._safe_string(event_info.get('date_utc')),
                    self._safe_string(event_info.get('patch')),
                    self._safe_string(team1.get('name')),
                    self._safe_string(team2.get('name')),
                    self._safe_int(team1.get('score_overall')),
                    self._safe_int(team2.get('score_overall')),
                    self._safe_string(match_data.get('match_format')),
                    self._safe_string(match_data.get('map_picks_bans_note')),
                    len(match_data.get('maps', [])),
                    self._safe_string(match_data.get('scraped_at'))
                ))

                # Clear existing map and player data for this match
                cursor.execute('DELETE FROM map_details WHERE match_id = ?', (match_id,))
                cursor.execute('DELETE FROM detailed_player_stats WHERE match_id = ?', (match_id,))

                # Save map details and player stats
                maps_data = match_data.get('maps', [])
                for map_data in maps_data:
                    # Save map details
                    cursor.execute('''
                        INSERT INTO map_details (
                            match_id, map_order, map_id, map_name, team1_score_map, team2_score_map,
                            winner_team_name, map_duration, picked_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match_id,
                        self._safe_int(map_data.get('map_order')),
                        self._safe_string(map_data.get('map_id')),
                        self._safe_string(map_data.get('map_name')),
                        self._safe_int(map_data.get('team1_score_map')),
                        self._safe_int(map_data.get('team2_score_map')),
                        self._safe_string(map_data.get('winner_team_name')),
                        self._safe_string(map_data.get('map_duration')),
                        self._safe_string(map_data.get('picked_by'))
                    ))

                    # Save player stats for this map
                    self._save_map_player_stats(cursor, match_id, map_data)

                # Save overall player stats
                overall_stats = match_data.get('overall_player_stats', {})
                for team_name, players in overall_stats.items():
                    for player in players:
                        self._save_player_detailed_stats(cursor, match_id, 'all', 'All Maps', player)

                return True

        except Exception as e:
            print(f"Error saving detailed match data: {e}")
            return False

    def _save_map_player_stats(self, cursor, match_id: str, map_data: Dict[str, Any]):
        """Save player stats for a specific map"""
        map_id = map_data.get('map_id')
        map_name = map_data.get('map_name')

        for team_name, players in map_data.get('player_stats', {}).items():
            for player in players:
                self._save_player_detailed_stats(cursor, match_id, map_id, map_name, player)

    def _save_player_detailed_stats(self, cursor, match_id: str, map_id: str, map_name: str, player: Dict[str, Any]):
        """Save detailed player statistics"""
        # Extract stats for all sides
        stats_all = player.get('stats_all_sides', {})
        stats_attack = player.get('stats_attack', {})
        stats_defense = player.get('stats_defense', {})

        cursor.execute('''
            INSERT INTO detailed_player_stats (
                match_id, map_id, map_name, team_name, player_id, player_name, agent, agents_list,
                rating_all, acs_all, kills_all, deaths_all, assists_all, kd_diff_all, kast_all, adr_all,
                hs_percent_all, first_kills_all, first_deaths_all, fk_fd_diff_all,
                rating_attack, acs_attack, kills_attack, deaths_attack, assists_attack, kd_diff_attack,
                kast_attack, adr_attack, hs_percent_attack, first_kills_attack, first_deaths_attack, fk_fd_diff_attack,
                rating_defense, acs_defense, kills_defense, deaths_defense, assists_defense, kd_diff_defense,
                kast_defense, adr_defense, hs_percent_defense, first_kills_defense, first_deaths_defense, fk_fd_diff_defense
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id,
            self._safe_string(map_id),
            self._safe_string(map_name),
            self._safe_string(player.get('team_name')),
            self._safe_string(player.get('player_id')),
            self._safe_string(player.get('player_name')),
            self._safe_string(player.get('agent')),
            self._safe_string(','.join(player.get('agents', []))),

            # All sides stats
            self._safe_float(stats_all.get('rating')),
            self._safe_float(stats_all.get('acs')),
            self._safe_int(stats_all.get('k')),
            self._safe_int(stats_all.get('d')),
            self._safe_int(stats_all.get('a')),
            self._safe_string(stats_all.get('kd_diff')),
            self._safe_string(stats_all.get('kast')),
            self._safe_float(stats_all.get('adr')),
            self._safe_string(stats_all.get('hs_percent')),
            self._safe_int(stats_all.get('fk')),
            self._safe_int(stats_all.get('fd')),
            self._safe_string(stats_all.get('fk_fd_diff')),

            # Attack stats
            self._safe_float(stats_attack.get('rating')),
            self._safe_float(stats_attack.get('acs')),
            self._safe_int(stats_attack.get('k')),
            self._safe_int(stats_attack.get('d')),
            self._safe_int(stats_attack.get('a')),
            self._safe_string(stats_attack.get('kd_diff')),
            self._safe_string(stats_attack.get('kast')),
            self._safe_float(stats_attack.get('adr')),
            self._safe_string(stats_attack.get('hs_percent')),
            self._safe_int(stats_attack.get('fk')),
            self._safe_int(stats_attack.get('fd')),
            self._safe_string(stats_attack.get('fk_fd_diff')),

            # Defense stats
            self._safe_float(stats_defense.get('rating')),
            self._safe_float(stats_defense.get('acs')),
            self._safe_int(stats_defense.get('k')),
            self._safe_int(stats_defense.get('d')),
            self._safe_int(stats_defense.get('a')),
            self._safe_string(stats_defense.get('kd_diff')),
            self._safe_string(stats_defense.get('kast')),
            self._safe_float(stats_defense.get('adr')),
            self._safe_string(stats_defense.get('hs_percent')),
            self._safe_int(stats_defense.get('fk')),
            self._safe_int(stats_defense.get('fd')),
            self._safe_string(stats_defense.get('fk_fd_diff'))
        ))

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to integer, return 0 for invalid values"""
        if value is None or value == '' or value == 'N/A' or value == 'n/a':
            return 0
        try:
            # Handle string values that might have extra characters
            if isinstance(value, str):
                # Remove common non-numeric characters but preserve negative sign
                cleaned = value.replace(',', '').strip()
                if cleaned == '' or cleaned.lower() == 'n/a':
                    return 0
                # Handle +/- prefixes
                if cleaned.startswith('+'):
                    cleaned = cleaned[1:]
            else:
                cleaned = str(value)
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float, return 0.0 for invalid values"""
        if value is None or value == '' or value == 'N/A' or value == 'n/a':
            return 0.0
        try:
            # Handle string values that might have extra characters
            if isinstance(value, str):
                # Handle percentage strings
                if '%' in value:
                    cleaned = value.replace('%', '').strip()
                else:
                    cleaned = value.replace(',', '').strip()

                if cleaned == '' or cleaned.lower() == 'n/a':
                    return 0.0
                # Handle +/- prefixes
                if cleaned.startswith('+'):
                    cleaned = cleaned[1:]
            else:
                cleaned = str(value)
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _safe_string(self, value: Any) -> str:
        """Safely convert value to string, return empty string for None/NA values"""
        if value is None or value == 'N/A' or value == 'n/a':
            return ''
        if isinstance(value, str):
            return value.strip()
        return str(value)
    
    def get_events_list(self) -> pd.DataFrame:
        """Get list of all events in database"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT event_id, title, dates, location, prize_pool, 
                       scraped_at, created_at
                FROM events 
                ORDER BY created_at DESC
            '''
            return pd.read_sql_query(query, conn)
    
    def get_event_data(self, event_id: str) -> Dict[str, pd.DataFrame]:
        """Get all data for a specific event"""
        with sqlite3.connect(self.db_path) as conn:
            data = {}

            # Event info
            event_query = 'SELECT * FROM events WHERE event_id = ?'
            data['event_info'] = pd.read_sql_query(event_query, conn, params=(event_id,))

            # Matches
            matches_query = 'SELECT * FROM matches WHERE event_id = ? ORDER BY created_at'
            data['matches'] = pd.read_sql_query(matches_query, conn, params=(event_id,))

            # Player stats
            stats_query = 'SELECT * FROM player_stats WHERE event_id = ? ORDER BY acs DESC'
            data['player_stats'] = pd.read_sql_query(stats_query, conn, params=(event_id,))

            # Agent usage
            agents_query = 'SELECT * FROM agent_usage WHERE event_id = ? ORDER BY usage_count DESC'
            data['agent_usage'] = pd.read_sql_query(agents_query, conn, params=(event_id,))

            # Detailed matches
            detailed_matches_query = 'SELECT * FROM detailed_matches WHERE event_id = ? ORDER BY created_at'
            data['detailed_matches'] = pd.read_sql_query(detailed_matches_query, conn, params=(event_id,))

            # Map details
            if not data['detailed_matches'].empty:
                match_ids = data['detailed_matches']['match_id'].tolist()
                if match_ids:
                    placeholders = ','.join(['?' for _ in match_ids])
                    map_details_query = f'SELECT * FROM map_details WHERE match_id IN ({placeholders}) ORDER BY match_id, map_order'
                    data['map_details'] = pd.read_sql_query(map_details_query, conn, params=match_ids)

                    # Detailed player stats
                    detailed_stats_query = f'SELECT * FROM detailed_player_stats WHERE match_id IN ({placeholders}) ORDER BY match_id, map_id, team_name, player_name'
                    data['detailed_player_stats'] = pd.read_sql_query(detailed_stats_query, conn, params=match_ids)
                else:
                    data['map_details'] = pd.DataFrame()
                    data['detailed_player_stats'] = pd.DataFrame()
            else:
                data['map_details'] = pd.DataFrame()
                data['detailed_player_stats'] = pd.DataFrame()

            return data
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Count events
            cursor.execute('SELECT COUNT(*) FROM events')
            stats['total_events'] = cursor.fetchone()[0]

            # Count matches
            cursor.execute('SELECT COUNT(*) FROM matches')
            stats['total_matches'] = cursor.fetchone()[0]

            # Count detailed matches
            cursor.execute('SELECT COUNT(*) FROM detailed_matches')
            stats['total_detailed_matches'] = cursor.fetchone()[0]

            # Count maps
            cursor.execute('SELECT COUNT(*) FROM map_details')
            stats['total_maps'] = cursor.fetchone()[0]

            # Count player records
            cursor.execute('SELECT COUNT(*) FROM player_stats')
            stats['total_player_records'] = cursor.fetchone()[0]

            # Count detailed player records
            cursor.execute('SELECT COUNT(*) FROM detailed_player_stats')
            stats['total_detailed_player_records'] = cursor.fetchone()[0]

            # Count agent records
            cursor.execute('SELECT COUNT(*) FROM agent_usage')
            stats['total_agent_records'] = cursor.fetchone()[0]

            # Count unique players
            cursor.execute('SELECT COUNT(DISTINCT player) FROM player_stats')
            stats['unique_players'] = cursor.fetchone()[0]

            # Count unique detailed players
            cursor.execute('SELECT COUNT(DISTINCT player_name) FROM detailed_player_stats')
            stats['unique_detailed_players'] = cursor.fetchone()[0]

            # Count unique teams
            cursor.execute('SELECT COUNT(DISTINCT team1) FROM matches')
            stats['unique_teams'] = cursor.fetchone()[0]

            return stats
    
    def export_to_csv(self, event_id: str, output_dir: str = "exports") -> List[str]:
        """Export event data to CSV files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        data = self.get_event_data(event_id)
        files_created = []
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for table_name, df in data.items():
            if not df.empty:
                filename = f"{output_dir}/{table_name}_{event_id}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                files_created.append(filename)
        
        return files_created
    
    def delete_event(self, event_id: str) -> bool:
        """Delete all data for a specific event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get match IDs for detailed matches
                cursor.execute('SELECT match_id FROM detailed_matches WHERE event_id = ?', (event_id,))
                match_ids = [row[0] for row in cursor.fetchall()]

                # Delete detailed match data
                if match_ids:
                    placeholders = ','.join(['?' for _ in match_ids])
                    cursor.execute(f'DELETE FROM detailed_player_stats WHERE match_id IN ({placeholders})', match_ids)
                    cursor.execute(f'DELETE FROM map_details WHERE match_id IN ({placeholders})', match_ids)

                # Delete in reverse order of dependencies
                cursor.execute('DELETE FROM detailed_matches WHERE event_id = ?', (event_id,))
                cursor.execute('DELETE FROM agent_usage WHERE event_id = ?', (event_id,))
                cursor.execute('DELETE FROM player_stats WHERE event_id = ?', (event_id,))
                cursor.execute('DELETE FROM matches WHERE event_id = ?', (event_id,))
                cursor.execute('DELETE FROM events WHERE event_id = ?', (event_id,))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")
            return False
    
    def get_database_size(self) -> str:
        """Get database file size in human readable format"""
        try:
            size_bytes = os.path.getsize(self.db_path)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            
            return f"{size_bytes:.1f} TB"

        except OSError:
            return "Unknown"

    def get_detailed_match_data(self, match_id: str) -> Dict[str, Any]:
        """Get comprehensive detailed match data for a specific match"""
        with sqlite3.connect(self.db_path) as conn:
            data = {}

            # Get match info
            match_query = 'SELECT * FROM detailed_matches WHERE match_id = ?'
            match_df = pd.read_sql_query(match_query, conn, params=(match_id,))

            if match_df.empty:
                return data

            data['match_info'] = match_df.iloc[0].to_dict()

            # Get map details
            map_query = 'SELECT * FROM map_details WHERE match_id = ? ORDER BY map_order'
            data['maps'] = pd.read_sql_query(map_query, conn, params=(match_id,))

            # Get player stats
            player_query = 'SELECT * FROM detailed_player_stats WHERE match_id = ? ORDER BY map_id, team_name, player_name'
            data['player_stats'] = pd.read_sql_query(player_query, conn, params=(match_id,))

            return data

    def get_player_performance_analysis(self, player_name: str = None, team_name: str = None, agent: str = None) -> pd.DataFrame:
        """Get player performance analysis with filtering options and proper agent aggregation"""
        with sqlite3.connect(self.db_path) as conn:
            # First get the basic player stats
            query = '''
                SELECT
                    dps.player_name,
                    dps.team_name,
                    dps.agent as primary_agent,
                    dps.map_name,
                    dm.event_name,
                    dm.team1_name,
                    dm.team2_name,
                    dps.rating_all,
                    dps.acs_all,
                    dps.kills_all,
                    dps.deaths_all,
                    dps.assists_all,
                    dps.kd_diff_all,
                    dps.kast_all,
                    dps.adr_all,
                    dps.hs_percent_all,
                    dps.first_kills_all,
                    dps.first_deaths_all,
                    dps.match_id,
                    dps.map_id
                FROM detailed_player_stats dps
                JOIN detailed_matches dm ON dps.match_id = dm.match_id
                WHERE 1=1
            '''

            params = []

            if player_name:
                query += ' AND dps.player_name LIKE ?'
                params.append(f'%{player_name}%')

            if team_name:
                query += ' AND dps.team_name LIKE ?'
                params.append(f'%{team_name}%')

            if agent:
                query += ' AND dps.agent LIKE ?'
                params.append(f'%{agent}%')

            query += ' ORDER BY dps.rating_all DESC'

            df = pd.read_sql_query(query, conn, params=params)

            if df.empty:
                return df

            # Now aggregate agents for each player-match-map combination
            agent_query = '''
                SELECT
                    player_name,
                    match_id,
                    map_id,
                    GROUP_CONCAT(DISTINCT agent) as all_agents
                FROM detailed_player_stats
                GROUP BY player_name, match_id, map_id
            '''

            agent_df = pd.read_sql_query(agent_query, conn)

            # Merge the agent data
            df = df.merge(agent_df, on=['player_name', 'match_id', 'map_id'], how='left')

            # Create agent display column
            def format_agent_display(row):
                if pd.isna(row['all_agents']) or row['all_agents'] == '':
                    return row['primary_agent']

                agents = row['all_agents'].split(',')
                unique_agents = list(set(agents))  # Remove duplicates

                if len(unique_agents) <= 3:
                    return ', '.join(unique_agents)
                else:
                    return f"{', '.join(unique_agents[:3])}, (+{len(unique_agents)-3})"

            df['agent_display'] = df.apply(format_agent_display, axis=1)
            df['agent_count'] = df['all_agents'].apply(lambda x: len(set(x.split(','))) if pd.notna(x) and x != '' else 1)

            # Clean up columns - remove redundant ones and rename for clarity
            df = df.drop(['match_id', 'map_id', 'all_agents'], axis=1)
            df = df.rename(columns={'primary_agent': 'agent'})

            return df

    def get_agent_performance_stats(self) -> pd.DataFrame:
        """Get comprehensive agent performance statistics"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT
                    agent,
                    COUNT(*) as times_played,
                    AVG(rating_all) as avg_rating,
                    AVG(acs_all) as avg_acs,
                    AVG(kills_all) as avg_kills,
                    AVG(deaths_all) as avg_deaths,
                    AVG(assists_all) as avg_assists,
                    AVG(adr_all) as avg_adr,
                    AVG(first_kills_all) as avg_first_kills,
                    AVG(first_deaths_all) as avg_first_deaths
                FROM detailed_player_stats
                WHERE map_id != 'all'  -- Exclude overall stats to avoid double counting
                GROUP BY agent
                HAVING COUNT(*) >= 5  -- Only agents played at least 5 times
                ORDER BY avg_rating DESC
            '''

            return pd.read_sql_query(query, conn)

    def get_map_performance_stats(self) -> pd.DataFrame:
        """Get map performance statistics"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT
                    md.map_name,
                    COUNT(*) as times_played,
                    AVG(md.team1_score_map + md.team2_score_map) as avg_total_rounds,
                    AVG(ABS(md.team1_score_map - md.team2_score_map)) as avg_round_diff,
                    COUNT(CASE WHEN ABS(md.team1_score_map - md.team2_score_map) <= 3 THEN 1 END) as close_games,
                    ROUND(COUNT(CASE WHEN ABS(md.team1_score_map - md.team2_score_map) <= 3 THEN 1 END) * 100.0 / COUNT(*), 2) as close_game_percentage
                FROM map_details md
                GROUP BY md.map_name
                ORDER BY times_played DESC
            '''

            return pd.read_sql_query(query, conn)


# Example usage and testing
if __name__ == "__main__":
    # Initialize database
    db = VLRDatabase("test_vlr_data.db")
    
    print("🗄️ VLR Database Manager Test")
    print("=" * 40)
    
    # Test database initialization
    print("✅ Database initialized successfully")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get database size
    size = db.get_database_size()
    print(f"💾 Database size: {size}")
    
    # List events
    events_df = db.get_events_list()
    print(f"📋 Events in database: {len(events_df)}")
    
    print("\n✅ Database manager is working correctly!")
