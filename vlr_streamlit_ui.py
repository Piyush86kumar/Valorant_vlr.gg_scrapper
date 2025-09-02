import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import io
import zipfile
from scrapper.vlr_scraper_coordinator import VLRScraperCoordinator
from scrapper.match_details_scrapper import MatchDetailsScraper

# Configure Streamlit page
st.set_page_config(
    page_title="VLR.gg Comprehensive Scraper",
    page_icon="🎮",
    layout="wide"
)

def init_session_state():
    """Initialize session state variables"""
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = None
    if 'scraping_progress' not in st.session_state:
        st.session_state.scraping_progress = 0
    if 'scraping_status' not in st.session_state:
        st.session_state.scraping_status = "Ready to scrape..."
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "idle"
    if 'scraper' not in st.session_state:
        st.session_state.scraper = VLRScraperCoordinator()
    if 'detailed_scraper' not in st.session_state:
        st.session_state.detailed_scraper = MatchDetailsScraper()
    if 'show_data_preview' not in st.session_state:
        st.session_state.show_data_preview = False
    if 'detailed_matches_data' not in st.session_state:
        st.session_state.detailed_matches_data = None

def display_header():
    """Display the main header"""
    st.title("🎮 VLR.gg Event Scraper")
    st.markdown("""
    ### Simple and efficient VLR.gg tournament data extraction

    **Three-step process**:
    1. **🔍 Scrape**: Extract data from VLR.gg event pages
    2. **👁️ Review**: Confirm what data was scraped
    3. **💾 Save**: Choose how to save your data
    """)
    st.divider()

def display_url_input():
    """Display URL input section"""
    st.header("📝 Event URL Input")

    col1, col2 = st.columns([4, 1])

    with col1:
        url = st.text_input(
            "VLR.gg Event URL:",
            placeholder="https://www.vlr.gg/event/2097/valorant-champions-2024",
            help="Enter the main VLR.gg event URL. The scraper will automatically access the matches, stats, and agents tabs.",
            key="main_url"
        )

    with col2:
        st.write("")  # Spacing
        validate_clicked = st.button("🔍 Validate", type="secondary")

    # URL validation
    if validate_clicked and url:
        is_valid, message = st.session_state.scraper.validate_url(url)

        if is_valid:
            st.success(f"✅ {message}")

            # Show constructed URLs
            try:
                # Extract event ID for URL construction
                import re
                match = re.search(r'/event/(\d+)/', url)
                if match:
                    event_id = match.group(1)
                    url_parts = url.split('/')
                    event_name = url_parts[-1] if url_parts[-1] else url_parts[-2]

                    st.info("📋 **URLs that will be scraped:**")
                    st.write(f"🏆 **Matches**: https://www.vlr.gg/event/matches/{event_id}/{event_name}")
                    st.write(f"📊 **Stats**: https://www.vlr.gg/event/stats/{event_id}/{event_name}")
                    st.write(f"🎭 **Agents**: https://www.vlr.gg/event/agents/{event_id}/{event_name}")
            except Exception as e:
                st.warning(f"Could not construct URLs: {e}")
        else:
            st.error(f"❌ {message}")
    elif validate_clicked:
        st.warning("Please enter a URL first")

    return url

def display_control_panel(url):
    """Display simple control panel with scraping options"""
    st.header("🔍 Step 1: Scrape Data")

    col1, col2 = st.columns([3, 1])

    with col1:
        # Simple scraping options
        st.markdown("**Select what to scrape:**")

        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        with col_a:
            scrape_matches = st.checkbox("🏆 Matches", value=True, help="Match results and scores")
        with col_b:
            scrape_stats = st.checkbox("📊 Player Stats", value=True, help="Individual player performance")
        with col_c:
            scrape_maps_agents = st.checkbox("🎭 Maps & Agents", value=True, help="Agent usage and map data")
        with col_d:
            scrape_detailed_matches = st.checkbox("🔍 Detailed Matches", value=True, help="Comprehensive match details from individual match pages")
        with col_e:
            scrape_economy = st.checkbox("💰 Economy", value=True, help="Scrape economy data for each match")
        with col_f:
            scrape_performance = st.checkbox("⚡ Performance", value=True, help="Scrape performance data for each match")

        # Show limit selector if any scraper that processes individual matches is enabled
        if scrape_detailed_matches or scrape_economy or scrape_performance:
            max_detailed_matches = st.selectbox(
                "Max matches to scrape:",
                [3, 5, 10, 15, 20, "All"],
                index=5,  # Default to All
                help="Limit the number of matches to scrape. Applies to detailed matches, economy, and performance data. 'All' will scrape every match in the tournament (may take a long time)"
            )

            # Show warning for "All" option
            if max_detailed_matches == "All":
                st.warning("⚠️ **Warning**: Selecting 'All' will scrape every match in the tournament and may take a long time.")
        else:
            max_detailed_matches = 0


    with col2:
        st.write("")  # Spacing
        scrape_clicked = st.button("🚀 Start Scraping", type="primary",
                                 disabled=not url or st.session_state.current_step == "scraping",
                                 use_container_width=True)

    # Clear data option (smaller)
    if st.session_state.scraped_data:
        if st.button("🗑️ Clear Previous Data", type="secondary"):
            st.session_state.scraped_data = None
            st.session_state.scraping_progress = 0
            st.session_state.scraping_status = "Ready to scrape..."
            st.session_state.current_step = "idle"
            st.rerun()

    # Get max detailed matches if detailed scraping is enabled
    max_detailed = max_detailed_matches if scrape_detailed_matches else 0

    return scrape_clicked, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed, scrape_economy, scrape_performance

def display_progress():
    """Display simple scraping progress"""
    if st.session_state.current_step == "scraping":
        st.header("⏳ Scraping in Progress...")

        # Progress bar
        progress_bar = st.progress(st.session_state.scraping_progress / 100)

        # Status text
        status_container = st.container()
        with status_container:
            st.text(st.session_state.scraping_status)

        return status_container

    elif st.session_state.scraped_data:
        st.header("✅ Scraping Completed!")

        # Simple summary
        data = st.session_state.scraped_data
        summary = st.session_state.scraper.get_scraping_summary(data)

        st.success(f"Successfully scraped data for: **{summary['event_title']}**")

        col1, col2, col3 = st.columns(3)
        with col1:
            if summary['total_matches'] > 0:
                st.info(f"🏆 **{summary['total_matches']}** matches found")
        with col2:
            if summary['total_players'] > 0:
                st.info(f"📊 **{summary['total_players']}** players found")
        with col3:
            if summary['total_agents'] > 0:
                st.info(f"🎭 **{summary['total_agents']}** agents found")

        return st.container()

    else:
        return st.container()

def perform_scraping(url, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed_matches, scrape_economy, scrape_performance, status_container):
    """Perform the actual scraping using the modular coordinator"""
    try:
        st.session_state.current_step = "scraping"

        # Progress callback function
        def update_progress(message):
            st.session_state.scraping_status = message
            with status_container:
                st.text(message)

        # Validate URL first
        is_valid, message = st.session_state.scraper.validate_url(url)
        if not is_valid:
            st.error(f"❌ {message}")
            st.session_state.current_step = "idle"
            return

        # Initialize progress
        st.session_state.scraping_progress = 10
        update_progress("Initializing modular scrapers...")

        # Use comprehensive scraping with selected modules
        st.session_state.scraping_progress = 20
        update_progress("Starting comprehensive scraping...")

        # Convert max_detailed_matches to proper format for coordinator
        max_matches_limit = None if max_detailed_matches == "All" else max_detailed_matches

        result = st.session_state.scraper.scrape_comprehensive(
            url,
            scrape_matches=scrape_matches,
            scrape_stats=scrape_stats,
            scrape_maps_agents=scrape_maps_agents,
            scrape_economy=scrape_economy,
            scrape_performance=scrape_performance,
            max_matches_limit=max_matches_limit,
            progress_callback=update_progress
        )

        # Detailed match scraping if requested
        if scrape_detailed_matches and result.get('matches_data', {}).get('matches'):
            st.session_state.scraping_progress = 80
            update_progress("🔍 Scraping detailed match data...")

            # Extract match URLs
            match_urls = []
            for match in result['matches_data']['matches']:
                match_url = match.get('match_url')
                if match_url:
                    match_urls.append(match_url)

            if match_urls:
                # Limit the number of matches to scrape (or scrape all if "All" is selected)
                if max_detailed_matches == "All":
                    urls_to_scrape = match_urls
                    update_progress(f"🔍 Found {len(match_urls)} matches, scraping ALL matches in detail...")
                    st.warning(f"⚠️ Scraping ALL {len(match_urls)} matches may take a very long time. Please be patient.")
                else:
                    urls_to_scrape = match_urls[:max_detailed_matches]
                    update_progress(f"🔍 Found {len(match_urls)} matches, scraping {len(urls_to_scrape)} in detail...")

                # Scrape detailed matches with progress tracking
                detailed_matches = []
                import time
                start_time = time.time()

                for i, match_url in enumerate(urls_to_scrape):
                    try:
                        # Calculate estimated time remaining
                        if i > 0:
                            elapsed_time = time.time() - start_time
                            avg_time_per_match = elapsed_time / i
                            remaining_matches = len(urls_to_scrape) - i
                            estimated_remaining = avg_time_per_match * remaining_matches

                            if estimated_remaining > 60:
                                time_str = f"~{estimated_remaining/60:.1f} min remaining"
                            else:
                                time_str = f"~{estimated_remaining:.0f} sec remaining"

                            progress_msg = f"🎯 Scraping detailed match {i+1}/{len(urls_to_scrape)} ({time_str}): {match_url.split('/')[-1]}"
                        else:
                            progress_msg = f"🎯 Scraping detailed match {i+1}/{len(urls_to_scrape)}: {match_url.split('/')[-1]}"

                        update_progress(progress_msg)
                        match_data = st.session_state.detailed_scraper.get_match_details(match_url)
                        detailed_matches.append(match_data)

                        # Small delay to avoid overwhelming the server
                        time.sleep(1)

                    except Exception as e:
                        update_progress(f"⚠️ Error scraping match {i+1}: {str(e)[:50]}...")
                        continue

                # Store detailed matches data
                st.session_state.detailed_matches_data = detailed_matches

                # Add to result
                result['detailed_matches'] = detailed_matches

                # Show completion message with timing
                total_time = time.time() - start_time
                if max_detailed_matches == "All":
                    update_progress(f"✅ Successfully scraped ALL {len(detailed_matches)} matches in {total_time/60:.1f} minutes!")
                else:
                    update_progress(f"✅ Successfully scraped {len(detailed_matches)} detailed matches in {total_time:.1f} seconds!")

                update_progress(f"✅ Scraped {len(detailed_matches)} detailed matches")

        # Complete
        st.session_state.scraping_progress = 100
        st.session_state.scraping_status = "✅ Comprehensive scraping completed successfully!"
        st.session_state.scraped_data = result
        st.session_state.current_step = "completed"

        # Show summary
        summary = st.session_state.scraper.get_scraping_summary(result)
        detailed_count = len(result.get('detailed_matches', []))
        detailed_text = f", {detailed_count} detailed matches" if detailed_count > 0 else ""
        st.success(f"✅ Data scraped successfully! Found {summary['total_matches']} matches, {summary['total_players']} players, {summary['total_agents']} agents{detailed_text}")
        st.rerun()

    except Exception as e:
        st.session_state.scraping_status = f"❌ Error: {str(e)}"
        st.session_state.current_step = "error"
        st.error(f"❌ Error during scraping: {str(e)}")

def display_simple_data_preview():
    """Display complete data preview for confirmation"""
    if not st.session_state.scraped_data:
        return

    st.header("👁️ Step 2: Review Scraped Data")
    data = st.session_state.scraped_data

    # Event info
    event_info = data.get('event_info', {})
    if event_info:
        st.subheader("📋 Event Information")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Title:** {event_info.get('title', 'N/A')}")
                st.write(f"**Dates:** {event_info.get('dates', 'N/A')}")
            with col2:
                st.write(f"**Location:** {event_info.get('location', 'N/A')}")
                st.write(f"**Prize Pool:** {event_info.get('prize_pool', 'N/A')}")

    # Matches data - show all
    matches_data = data.get('matches_data', {})
    if matches_data and matches_data.get('matches'):
        st.subheader("🏆 Matches Data")
        matches = matches_data['matches']

        with st.container(border=True):
            st.write(f"**Total matches found:** {len(matches)}")

            # Show all matches in a table
            if matches:
                matches_df = pd.DataFrame(matches)
                display_columns = ['match_id', 'date', 'time', 'team1', 'score', 'team2', 'winner', 'status', 'week', 'stage', 'match_url']
                available_columns = [col for col in display_columns if col in matches_df.columns]

                st.dataframe(
                    matches_df[available_columns],
                    use_container_width=True,
                    hide_index=True
                )

    # Detailed matches data - show all, RAW, no summary, no aggregation, all columns/rows
    detailed_matches = data.get('detailed_matches', [])
    if detailed_matches:
        st.subheader("🔍 Detailed Matches Data (Raw)")
        st.info("Below is the exact, raw detailed match data as scraped. All columns and rows are shown, with no aggregation or filtering. Please review before saving.")

        for i, match in enumerate(detailed_matches):
            teams = match.get('teams', {})
            team1_name = teams.get('team1', {}).get('name', 'Team 1')
            team2_name = teams.get('team2', {}).get('name', 'Team 2')
            team1_score = teams.get('team1', {}).get('score_overall', 0)
            team2_score = teams.get('team2', {}).get('score_overall', 0)

            with st.expander(f"Match {i+1}: {team1_name} vs {team2_name}", expanded=i==0):
                # Match info
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Match ID:** {match.get('match_id', 'N/A')}")
                    st.write(f"**Event:** {match.get('event_info', {}).get('name', 'N/A')}")
                    st.write(f"**Date:** {match.get('event_info', {}).get('date_utc', 'N/A')}")
                    st.write(f"**Format:** {match.get('match_format', 'N/A')}")

                with col2:
                    st.write(f"**Teams:** {team1_name} vs {team2_name}")
                    st.write(f"**Score:** {team1_score} - {team2_score}")
                    st.write(f"**Maps Played:** {len(match.get('maps', []))}")
                    st.write(f"**Patch:** {match.get('event_info', {}).get('patch', 'N/A')}")

                if match.get('match_url'):
                    st.markdown(f"🔗 **[View on VLR.gg]({match.get('match_url')})**")

                # Map picks/bans info
                if match.get('map_picks_bans_note'):
                    st.write(f"**Pick/Ban Info:** {match.get('map_picks_bans_note')}")

                # Show raw overall player stats
                overall_stats = match.get('overall_player_stats', {})
                if overall_stats:
                    st.markdown("**Overall Player Stats (All Maps Combined):**")

                    # Flatten overall stats for display - INCLUDING ALL FILTERS (All/Attack/Defense)
                    all_overall_stats = []
                    for team_name, players in overall_stats.items():
                        for player in players:
                            # Flatten the nested stats structure
                            flat_player = {
                                'Team': player.get('team_name', team_name),
                                'Player': player.get('player_name', 'Unknown'),
                                'Player ID': player.get('player_id', 'N/A'),
                                'Agent': ', '.join(player.get('agents', [])) if player.get('agents') else player.get('agent', 'N/A'),
                            }

                            # Add all sides stats (All filter)
                            stats_all = player.get('stats_all_sides', {})
                            for key, value in stats_all.items():
                                flat_player[f'All_{key}'] = value

                            # Add attack stats (Attack filter)
                            stats_attack = player.get('stats_attack', {})
                            for key, value in stats_attack.items():
                                flat_player[f'Attack_{key}'] = value

                            # Add defense stats (Defense filter)
                            stats_defense = player.get('stats_defense', {})
                            for key, value in stats_defense.items():
                                flat_player[f'Defense_{key}'] = value

                            all_overall_stats.append(flat_player)

                    if all_overall_stats:
                        overall_df = pd.DataFrame(all_overall_stats)
                        st.dataframe(overall_df, use_container_width=True, hide_index=True)

                # Show raw map-by-map stats
                maps_data = match.get('maps', [])
                if maps_data:
                    st.markdown("**Map-by-Map Player Stats:**")

                    for map_data in maps_data:
                        st.markdown(f"**{map_data.get('map_name', 'Unknown Map')} (Order: {map_data.get('map_order', 'N/A')})**")
                        st.write(f"Score: {map_data.get('team1_score_map', 0)} - {map_data.get('team2_score_map', 0)}")
                        st.write(f"Winner: {map_data.get('winner_team_name', 'N/A')}")
                        st.write(f"Duration: {map_data.get('map_duration', 'N/A')}")
                        st.write(f"Picked by: {map_data.get('picked_by', 'N/A')}")

                        # Flatten map player stats - INCLUDING ALL FILTERS (All/Attack/Defense)
                        map_player_stats = []
                        for team_name, players in map_data.get('player_stats', {}).items():
                            for player in players:
                                flat_player = {
                                    'Team': player.get('team_name', team_name),
                                    'Player': player.get('player_name', 'Unknown'),
                                    'Player ID': player.get('player_id', 'N/A'),
                                    'Agent': player.get('agent', 'N/A'),
                                }

                                # Add all sides stats (All filter)
                                stats_all = player.get('stats_all_sides', {})
                                for key, value in stats_all.items():
                                    flat_player[f'All_{key}'] = value

                                # Add attack stats (Attack filter)
                                stats_attack = player.get('stats_attack', {})
                                for key, value in stats_attack.items():
                                    flat_player[f'Attack_{key}'] = value

                                # Add defense stats (Defense filter)
                                stats_defense = player.get('stats_defense', {})
                                for key, value in stats_defense.items():
                                    flat_player[f'Defense_{key}'] = value

                                map_player_stats.append(flat_player)

                        if map_player_stats:
                            map_df = pd.DataFrame(map_player_stats)
                            st.dataframe(map_df, use_container_width=True, hide_index=True)

    # Player stats data - show all
    stats_data = data.get('stats_data', {})
    if stats_data and stats_data.get('player_stats'):
        st.subheader("📊 Player Statistics")
        players = stats_data['player_stats']

        with st.container(border=True):
            st.write(f"**Total players found:** {len(players)}")

            # Show all players in a table
            if players:
                players_df = pd.DataFrame(players)
                display_columns = [
                    'player_id', 'player', 'team', 'agents_display', 'rating', 'acs', 'kd_ratio', 'kast', 'adr',
                    'kills', 'deaths', 'assists', 'rounds', 'kpr', 'apr',
                    'fkpr', 'fdpr', 'hs_percent', 'cl_percent', 'clutches',
                    'k_max', 'first_kills', 'first_deaths', 'agents_count'
                ]
                available_columns = [col for col in display_columns if col in players_df.columns]

                st.dataframe(
                    players_df[available_columns],
                    use_container_width=True,
                    hide_index=True
                )

    # Maps & Agents data - show all (updated for new structure)
    maps_agents_data = data.get('maps_agents_data', {})

    # Handle new structure (maps and agents) or old structure (agent_stats and map_stats)
    agents = maps_agents_data.get('agents', maps_agents_data.get('agent_stats', []))
    maps = maps_agents_data.get('maps', maps_agents_data.get('map_stats', []))

    if agents:
        st.subheader("🎭 Agent Utilization Statistics")

        with st.container(border=True):
            st.write(f"**Total agents found:** {len(agents)}")

            # Transform agent data for better display in a wide, tabular format
            vlr_table_data = []
            all_map_columns = set()

            for agent in agents:
                row_data = {
                    'Agent': agent.get('agent_name', agent.get('agent', 'Unknown')),
                    'Total Utilization (%)': agent.get('total_utilization', 0)
                }

                map_utils_raw = agent.get('map_utilizations', {})
                
                map_details = {}
                # Handle if map_utilizations is a stringified JSON
                if isinstance(map_utils_raw, str):
                    try:
                        map_details = json.loads(map_utils_raw)
                    except json.JSONDecodeError:
                        map_details = {}
                elif isinstance(map_utils_raw, dict):
                    map_details = map_utils_raw
                elif isinstance(map_utils_raw, list):
                    # Convert from [{'map': name, 'utilization_percent': val}] to {name: val}
                    for item in map_utils_raw:
                        if isinstance(item, dict) and 'map' in item and 'utilization_percent' in item:
                            map_details[item['map']] = item['utilization_percent']
                
                if isinstance(map_details, dict):
                    row_data.update(map_details)
                    all_map_columns.update(map_details.keys())

                vlr_table_data.append(row_data)

            if vlr_table_data:
                final_df = pd.DataFrame(vlr_table_data)
                cols_ordered = ['Agent', 'Total Utilization (%)'] + sorted(list(all_map_columns))
                final_df = final_df.reindex(columns=cols_ordered).fillna(0)
                st.dataframe(final_df, use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame(agents), use_container_width=True, hide_index=True)

    if maps:
        st.subheader("🗺️ Map Statistics")

        with st.container(border=True):
            st.write(f"**Total maps found:** {len(maps)}")

            maps_df = pd.DataFrame(maps)
            st.dataframe(maps_df, use_container_width=True, hide_index=True)
            
    # Economy data
    economy_data = data.get('economy_data', [])
    if economy_data:
        st.subheader("💰 Economy Data")
        with st.container(border=True):
            st.write(f"**Total economy records found:** {len(economy_data)}")
            if economy_data:
                # Check if economy_data is a list of dictionaries (new format) or nested structure (old format)
                if isinstance(economy_data, list) and len(economy_data) > 0:
                    first_item = economy_data[0]
                    if isinstance(first_item, dict) and 'economy_data' in first_item:
                        # Old nested format
                        flat_economy_data = []
                        for item in economy_data:
                            match_id = item.get('match_id', 'N/A')
                            for record in item.get('economy_data', []):
                                record['match_id'] = match_id
                                flat_economy_data.append(record)
                    else:
                        # New flat format - economy_data is already a list of records
                        flat_economy_data = economy_data

                if flat_economy_data:
                    economy_df = pd.DataFrame(flat_economy_data)
                    # Rename columns for better display
                    economy_df = economy_df.rename(columns={
                        'Pistol Won': 'Pistol Won',
                        'Eco (won)': 'Eco (won)',
                        'Semi-eco (won)': 'Semi-eco: 5-10k',
                        'Semi-buy (won)': 'Semi-buy: 10-20k',
                        'Full buy(won)': 'Full buy: 20k+'
                    })
                    st.dataframe(economy_df, use_container_width=True, hide_index=True)

    # Performance data
    performance_data_container = data.get('performance_data', {})
    performance_data_list = performance_data_container.get('matches', [])

    if performance_data_list:
        st.subheader("⚡ Performance Data")
        with st.container(border=True):
            st.write(f"**Total performance matches found:** {len(performance_data_list)}")

            # Flatten the performance data for display
            flat_performance_data = []
            total_players = 0

            for item in performance_data_list:
                match_id = item.get('match_id', 'N/A')
                match_info = item.get('match_info', {})

                for map_key, map_data in item.get('performance_data', {}).items():
                    map_name = map_data.get('map_name', 'N/A')
                    performance_stats = map_data.get('performance_stats', {})

                    for player_type in ['team1_players', 'team2_players']:
                        for player_stats in performance_stats.get(player_type, []):
                            flat_player = {
                                'Match ID': match_id,
                                'Map': map_name,
                                'Player': player_stats.get('player_name', 'N/A'),
                                'Team': player_stats.get('team_name', match_info.get('team1', 'Team 1') if player_type == 'team1_players' else match_info.get('team2', 'Team 2')),
                                'Agent': player_stats.get('agent', 'N/A'),
                                '2K': player_stats.get('multikills', {}).get('2k', 0),
                                '3K': player_stats.get('multikills', {}).get('3k', 0),
                                '4K': player_stats.get('multikills', {}).get('4k', 0),
                                '5K': player_stats.get('multikills', {}).get('5k', 0),
                                '1v1': player_stats.get('clutches', {}).get('1v1', 0),
                                '1v2': player_stats.get('clutches', {}).get('1v2', 0),
                                '1v3': player_stats.get('clutches', {}).get('1v3', 0),
                                '1v4': player_stats.get('clutches', {}).get('1v4', 0),
                                '1v5': player_stats.get('clutches', {}).get('1v5', 0),
                                'ECON': player_stats.get('other_stats', {}).get('econ', 0),
                                'PL': player_stats.get('other_stats', {}).get('pl', 0),
                                'DE': player_stats.get('other_stats', {}).get('de', 0),
                            }
                            flat_performance_data.append(flat_player)
                            total_players += 1

            if flat_performance_data:
                # Create DataFrame and clean data
                performance_df = pd.DataFrame(flat_performance_data)

                # Clean and validate numeric columns to prevent overflow errors
                numeric_columns = ['2K', '3K', '4K', '5K', '1v1', '1v2', '1v3', '1v4', '1v5', 'ECON', 'PL', 'DE']
                for col in numeric_columns:
                    if col in performance_df.columns:
                        # Convert to numeric, replacing invalid values with 0
                        performance_df[col] = pd.to_numeric(performance_df[col], errors='coerce').fillna(0)
                        # Convert to int (no capping to prevent data corruption)
                        performance_df[col] = performance_df[col].astype(int)



                # Display the dataframe with better formatting
                st.dataframe(
                    performance_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Match ID": st.column_config.TextColumn("Match ID", width="small"),
                        "Map": st.column_config.TextColumn("Map", width="small"),
                        "Player": st.column_config.TextColumn("Player", width="medium"),
                        "Team": st.column_config.TextColumn("Team", width="medium"),
                        "Agent": st.column_config.TextColumn("Agent", width="small"),
                        "2K": st.column_config.NumberColumn("2K", width="small"),
                        "3K": st.column_config.NumberColumn("3K", width="small"),
                        "4K": st.column_config.NumberColumn("4K", width="small"),
                        "5K": st.column_config.NumberColumn("5K", width="small"),
                        "1v1": st.column_config.NumberColumn("1v1", width="small"),
                        "1v2": st.column_config.NumberColumn("1v2", width="small"),
                        "1v3": st.column_config.NumberColumn("1v3", width="small"),
                        "1v4": st.column_config.NumberColumn("1v4", width="small"),
                        "1v5": st.column_config.NumberColumn("1v5", width="small"),
                        "ECON": st.column_config.NumberColumn("ECON", width="small"),
                        "PL": st.column_config.NumberColumn("PL", width="small"),
                        "DE": st.column_config.NumberColumn("DE", width="small"),
                    }
                )


            else:
                st.warning("⚠️ **Performance data extraction issue detected**")
                st.info("The performance scraper found match data but couldn't extract player statistics. This may be due to changes in VLR.gg's HTML structure. The performance scraper may need to be updated to work with the current website format.")
                # Show raw data for debugging
                with st.expander("Show Raw Performance Data for Debugging"):
                    st.json(performance_data_list)
                # Show raw data for debugging
                with st.expander("Show Raw Performance Data for Debugging"):
                    st.json(performance_data_list)
                # Show raw data for debugging
                with st.expander("Show Raw Performance Data for Debugging"):
                    st.json(performance_data_list)
    else:
        # Show message when no performance data is available
        if data.get('performance_data'):
            st.subheader("⚡ Performance Data")
            with st.container(border=True):
                st.info("Performance data structure found but no match records available.")
        # If performance scraping wasn't enabled, don't show anything



def display_save_options():
    """Display 2 main save options as requested"""
    if not st.session_state.scraped_data:
        return

    st.header("💾 Step 3: Save Your Data")

    st.markdown("Choose how you want to save the scraped data:")

    # 2 main options in columns
    col1, col2 = st.columns(2)

    data = st.session_state.scraped_data

    # Option 1: Download as CSVs (now first and default)
    with col1:
        st.subheader("📊 Download as CSVs")
        st.markdown("**[DEFAULT]** Download data as a ZIP file containing multiple CSVs")
        # Prepare CSV data
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Event info
            if 'event_info' in data:
                df = pd.DataFrame([data['event_info']])
                zip_file.writestr("event_info.csv", df.to_csv(index=False))

            # Matches
            if data.get('matches_data', {}).get('matches'):
                df = pd.DataFrame(data['matches_data']['matches'])
                zip_file.writestr("matches.csv", df.to_csv(index=False))

            # Player Stats
            if data.get('stats_data', {}).get('player_stats'):
                df = pd.DataFrame(data['stats_data']['player_stats'])
                zip_file.writestr("player_stats.csv", df.to_csv(index=False))

            # Maps & Agents
            if data.get('maps_agents_data', {}).get('maps'):
                df = pd.DataFrame(data['maps_agents_data']['maps'])
                zip_file.writestr("maps_stats.csv", df.to_csv(index=False))
            if data.get('maps_agents_data', {}).get('agents'):
                df = pd.DataFrame(data['maps_agents_data']['agents'])
                zip_file.writestr("agents_stats.csv", df.to_csv(index=False))

            # Detailed Matches
            if 'detailed_matches' in data and data['detailed_matches']:
                # Create detailed match overview CSV
                match_overview_data = []
                map_details_data = []
                
                for match in data['detailed_matches']:
                    teams = match.get('teams', {})
                    team1_name = teams.get('team1', {}).get('name', 'Team 1')
                    team2_name = teams.get('team2', {}).get('name', 'Team 2')
                    team1_score = teams.get('team1', {}).get('score_overall', 0)
                    team2_score = teams.get('team2', {}).get('score_overall', 0)
                    event_info = match.get('event_info', {})
                    
                    # Match overview row
                    match_overview = {
                        'match_id': match.get('match_id', 'N/A'),
                        'match_title': f"{team1_name} vs {team2_name}",
                        'event': event_info.get('name', 'N/A'),
                        'date': event_info.get('date_utc', 'N/A'),
                        'format': match.get('match_format', 'N/A'),
                        'teams': f"{team1_name} vs {team2_name}",
                        'score': f"{team1_score} - {team2_score}",
                        'maps_played': len(match.get('maps', [])),
                        'patch': event_info.get('patch', 'N/A'),
                        'pick_ban_info': match.get('map_picks_bans_note', 'N/A'),
                        'match_url': match.get('match_url', 'N/A')
                    }
                    match_overview_data.append(match_overview)
                    
                    # Map details for this match
                    for map_data in match.get('maps', []):
                        map_detail = {
                            'match_id': match.get('match_id', 'N/A'),
                            'map_name': map_data.get('map_name', 'Unknown Map'),
                            'map_order': map_data.get('map_order', 'N/A'),
                            'score': f"{map_data.get('team1_score_map', 0)} - {map_data.get('team2_score_map', 0)}",
                            'winner': map_data.get('winner_team_name', 'N/A'),
                            'duration': map_data.get('map_duration', 'N/A'),
                            'picked_by': map_data.get('picked_by', 'N/A')
                        }
                        map_details_data.append(map_detail)
                
                # Save match overview CSV
                if match_overview_data:
                    overview_df = pd.DataFrame(match_overview_data)
                    zip_file.writestr("detailed_matches_overview.csv", overview_df.to_csv(index=False))
                
                # Save map details CSV
                if map_details_data:
                    maps_df = pd.DataFrame(map_details_data)
                    zip_file.writestr("detailed_matches_maps.csv", maps_df.to_csv(index=False))
                
                # Create a flattened DataFrame for detailed player stats (existing functionality)
                flat_detailed = []
                for match in data['detailed_matches']:
                    # Basic match info
                    base_info = {
                        'match_id': match.get('match_id'),
                        'event_name': match.get('event_info', {}).get('name'),
                        'event_stage': match.get('event_info', {}).get('stage'),
                        'match_date': match.get('event_info', {}).get('date_utc'),
                        'team1': match.get('teams', {}).get('team1', {}).get('name'),
                        'team2': match.get('teams', {}).get('team2', {}).get('name'),
                        'score_overall': f"{match.get('teams', {}).get('team1', {}).get('score_overall', 0)} - {match.get('teams', {}).get('team2', {}).get('score_overall', 0)}"
                    }
                    
                    # Overall player stats
                    for team_name, players in match.get('overall_player_stats', {}).items():
                        for player in players:
                            p_info = base_info.copy()
                            p_info.update({
                                'player_name': player.get('player_name'),
                                'player_id': player.get('player_id', 'N/A'),
                                'player_team': team_name,
                                'stat_type': 'overall',
                                'agent': ', '.join(player.get('agents', [])) if player.get('agents') else player.get('agent', 'N/A')
                            })
                            p_info.update(player.get('stats_all_sides', {}))
                            flat_detailed.append(p_info)
                    
                    # Map-by-map player stats
                    for map_data in match.get('maps', []):
                        map_info = base_info.copy()
                        map_info.update({
                            'map_name': map_data.get('map_name'),
                            'map_winner': map_data.get('winner_team_name')
                        })
                        for team_name, players in map_data.get('player_stats', {}).items():
                            for player in players:
                                p_info = map_info.copy()
                                p_info.update({
                                    'player_name': player.get('player_name'),
                                    'player_id': player.get('player_id', 'N/A'),
                                    'player_team': team_name,
                                    'stat_type': 'map',
                                    'agent': player.get('agent', 'N/A')
                                })
                                p_info.update(player.get('stats_all_sides', {}))
                                flat_detailed.append(p_info)

                if flat_detailed:
                    df = pd.DataFrame(flat_detailed)
                    zip_file.writestr("detailed_matches_player_stats.csv", df.to_csv(index=False))

            # Economy Data
            if 'economy_data' in data and data['economy_data']:
                # Check if economy_data is a list of dictionaries (new format) or nested structure (old format)
                if isinstance(data['economy_data'], list) and len(data['economy_data']) > 0:
                    first_item = data['economy_data'][0]
                    if isinstance(first_item, dict) and 'economy_data' in first_item:
                        # Old nested format
                        flat_economy_data = []
                        for item in data['economy_data']:
                            match_id = item.get('match_id', 'N/A')
                            for record in item.get('economy_data', []):
                                record['match_id'] = match_id
                                flat_economy_data.append(record)
                    else:
                        # New flat format - economy_data is already a list of records
                        flat_economy_data = data['economy_data']

                    if flat_economy_data:
                        economy_df = pd.DataFrame(flat_economy_data)
                        zip_file.writestr("economy_data.csv", economy_df.to_csv(index=False))

            # Performance Data
            if 'performance_data' in data and data['performance_data']:
                performance_data_list_for_csv = data['performance_data'].get('matches', [])
                if performance_data_list_for_csv:
                    flat_performance_data = []
                    for item in performance_data_list_for_csv:
                        match_id = item.get('match_id', 'N/A')
                        match_info = item.get('match_info', {})

                        for map_key, map_data in item.get('performance_data', {}).items():
                            map_name = map_data.get('map_name', 'N/A')

                            performance_stats = map_data.get('performance_stats', {})

                            for player_type in ['team1_players', 'team2_players']:
                                for player_stats in performance_stats.get(player_type, []):
                                    flat_player = {
                                        'Match ID': match_id,
                                        'Map': map_name,
                                        'Player': player_stats.get('player_name', 'N/A'),
                                        'Team': player_stats.get('team_name', match_info.get('team1', 'Team 1') if player_type == 'team1_players' else match_info.get('team2', 'Team 2')),
                                        'Agent': player_stats.get('agent', 'N/A'),
                                        '2K': player_stats.get('multikills', {}).get('2k', 0),
                                        '3K': player_stats.get('multikills', {}).get('3k', 0),
                                        '4K': player_stats.get('multikills', {}).get('4k', 0),
                                        '5K': player_stats.get('multikills', {}).get('5k', 0),
                                        '1v1': player_stats.get('clutches', {}).get('1v1', 0),
                                        '1v2': player_stats.get('clutches', {}).get('1v2', 0),
                                        '1v3': player_stats.get('clutches', {}).get('1v3', 0),
                                        '1v4': player_stats.get('clutches', {}).get('1v4', 0),
                                        '1v5': player_stats.get('clutches', {}).get('1v5', 0),
                                        'ECON': player_stats.get('other_stats', {}).get('econ', 0),
                                        'PL': player_stats.get('other_stats', {}).get('pl', 0),
                                        'DE': player_stats.get('other_stats', {}).get('de', 0),
                                    }
                                    flat_performance_data.append(flat_player)
                    if flat_performance_data:
                        performance_df = pd.DataFrame(flat_performance_data)

                        # Clean and validate numeric columns to prevent overflow errors
                        numeric_columns = ['2K', '3K', '4K', '5K', '1v1', '1v2', '1v3', '1v4', '1v5', 'ECON', 'PL', 'DE']
                        for col in numeric_columns:
                                # Convert to numeric, replacing invalid values with 0
                                performance_df[col] = pd.to_numeric(performance_df[col], errors='coerce').fillna(0)
                                # Cap extremely large values to prevent overflow (max 999999)
                                performance_df[col] = performance_df[col].clip(upper=999999)
                                # Convert to int
                                performance_df[col] = performance_df[col].astype(int)

                        zip_file.writestr("performance_data.csv", performance_df.to_csv(index=False))

        zip_buffer.seek(0)
        
        # Get event name for filename
        event_title = data.get('event_info', {}).get('title', 'vlr_data')
        safe_event_title = "".join(c for c in event_title if c.isalnum() or c in (' ', '_')).rstrip()
        
        st.download_button(
            label="📥 Download CSVs (ZIP)",
            data=zip_buffer,
            file_name=f"{safe_event_title}_csvs.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )

    # Option 2: Download as JSON
    with col2:
        st.subheader("📄 Download as JSON")
        st.markdown("Download all scraped data as a single JSON file")

        # Prepare enhanced JSON data with same structure as CSV files
        enhanced_data = data.copy()
        
        # Add detailed match overview and map data (same as CSV structure)
        if 'detailed_matches' in enhanced_data and enhanced_data['detailed_matches']:
            match_overview_data = []
            map_details_data = []
            detailed_player_stats = []
            
            for match in enhanced_data['detailed_matches']:
                teams = match.get('teams', {})
                team1_name = teams.get('team1', {}).get('name', 'Team 1')
                team2_name = teams.get('team2', {}).get('name', 'Team 2')
                team1_score = teams.get('team1', {}).get('score_overall', 0)
                team2_score = teams.get('team2', {}).get('score_overall', 0)
                event_info = match.get('event_info', {})
                
                # Match overview
                match_overview = {
                    'match_id': match.get('match_id', 'N/A'),
                    'match_title': f"{team1_name} vs {team2_name}",
                    'event': event_info.get('name', 'N/A'),
                    'date': event_info.get('date_utc', 'N/A'),
                    'format': match.get('match_format', 'N/A'),
                    'teams': f"{team1_name} vs {team2_name}",
                    'score': f"{team1_score} - {team2_score}",
                    'maps_played': len(match.get('maps', [])),
                    'patch': event_info.get('patch', 'N/A'),
                    'pick_ban_info': match.get('map_picks_bans_note', 'N/A'),
                    'match_url': match.get('match_url', 'N/A')
                }
                match_overview_data.append(match_overview)
                
                # Map details
                for map_data in match.get('maps', []):
                    map_detail = {
                        'match_id': match.get('match_id', 'N/A'),
                        'map_name': map_data.get('map_name', 'Unknown Map'),
                        'map_order': map_data.get('map_order', 'N/A'),
                        'score': f"{map_data.get('team1_score_map', 0)} - {map_data.get('team2_score_map', 0)}",
                        'winner': map_data.get('winner_team_name', 'N/A'),
                        'duration': map_data.get('map_duration', 'N/A'),
                        'picked_by': map_data.get('picked_by', 'N/A')
                    }
                    map_details_data.append(map_detail)
                
                # Detailed player stats (same structure as CSV)
                base_info = {
                    'match_id': match.get('match_id'),
                    'event_name': match.get('event_info', {}).get('name'),
                    'event_stage': match.get('event_info', {}).get('stage'),
                    'match_date': match.get('event_info', {}).get('date_utc'),
                    'team1': match.get('teams', {}).get('team1', {}).get('name'),
                    'team2': match.get('teams', {}).get('team2', {}).get('name'),
                    'score_overall': f"{match.get('teams', {}).get('team1', {}).get('score_overall', 0)} - {match.get('teams', {}).get('team2', {}).get('score_overall', 0)}"
                }
                
                # Overall player stats
                for team_name, players in match.get('overall_player_stats', {}).items():
                    for player in players:
                        p_info = base_info.copy()
                        p_info.update({
                            'player_name': player.get('player_name'),
                            'player_id': player.get('player_id', 'N/A'),
                            'player_team': team_name,
                            'stat_type': 'overall',
                            'agent': ', '.join(player.get('agents', [])) if player.get('agents') else player.get('agent', 'N/A')
                        })
                        p_info.update(player.get('stats_all_sides', {}))
                        detailed_player_stats.append(p_info)
                
                # Map-by-map player stats
                for map_data in match.get('maps', []):
                    map_info = base_info.copy()
                    map_info.update({
                        'map_name': map_data.get('map_name'),
                        'map_winner': map_data.get('winner_team_name')
                    })
                    for team_name, players in map_data.get('player_stats', {}).items():
                        for player in players:
                            p_info = map_info.copy()
                            p_info.update({
                                'player_name': player.get('player_name'),
                                'player_id': player.get('player_id', 'N/A'),
                                'player_team': team_name,
                                'stat_type': 'map',
                                'agent': player.get('agent', 'N/A')
                            })
                            p_info.update(player.get('stats_all_sides', {}))
                            detailed_player_stats.append(p_info)
            
            # Add structured overview data to JSON
            enhanced_data['detailed_matches_overview'] = match_overview_data
            enhanced_data['detailed_matches_maps'] = map_details_data
            enhanced_data['detailed_matches_player_stats'] = detailed_player_stats
        
        json_string = json.dumps(enhanced_data, indent=4)
        
        # Get event name for filename
        event_title = enhanced_data.get('event_info', {}).get('title', 'vlr_data')
        safe_event_title = "".join(c for c in event_title if c.isalnum() or c in (' ', '_')).rstrip()
        
        st.download_button(
            label="📥 Download JSON",
            data=json_string,
            file_name=f"{safe_event_title}.json",
            mime="application/json",
            use_container_width=True
        )

def main():
    """Main function to run the Streamlit app"""
    init_session_state()
    display_header()

    # Main scraper interface (no navigation needed)
    url = display_url_input()
    scrape_clicked, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed, max_detailed, scrape_economy, scrape_performance = display_control_panel(url)
    status_container = display_progress()

    if scrape_clicked:
        perform_scraping(url, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed, max_detailed, scrape_economy, scrape_performance, status_container)

    if st.session_state.scraped_data:
        st.divider()
        display_simple_data_preview()
        st.divider()
        display_save_options()

if __name__ == "__main__":
    main()
