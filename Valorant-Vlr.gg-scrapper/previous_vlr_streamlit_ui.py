import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import io
import zipfile
from vlr_scraper_coordinator import VLRScraperCoordinator
from match_details_scrapper import MatchDetailsScraper
from vlr_database import VLRDatabase

# Configure Streamlit page
st.set_page_config(
    page_title="VLR.gg Comprehensive Scraper",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
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
    if 'db' not in st.session_state:
        st.session_state.db = VLRDatabase()
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

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            scrape_matches = st.checkbox("🏆 Matches", value=True, help="Match results and scores")
        with col_b:
            scrape_stats = st.checkbox("📊 Player Stats", value=True, help="Individual player performance")
        with col_c:
            scrape_maps_agents = st.checkbox("🎭 Maps & Agents", value=True, help="Agent usage and map data")
        with col_d:
            scrape_detailed_matches = st.checkbox("🔍 Detailed Matches", value=False, help="Comprehensive match details from individual match pages")
            if scrape_detailed_matches:
                max_detailed_matches = st.selectbox(
                    "Max detailed matches to scrape:",
                    [3, 5, 10, 15, 20, "All"],
                    index=1,  # Default to 5
                    help="Limit the number of matches to scrape in detail. 'All' will scrape every match in the tournament (may take a long time)"
                )

                # Show warning for "All" option
                if max_detailed_matches == "All":
                    st.warning("⚠️ **Warning**: Selecting 'All' will scrape every match in the tournament. This may take 30+ minutes for large tournaments and will make many requests to VLR.gg. Use responsibly!")
                    st.info("💡 **Tip**: For testing or quick analysis, consider using a smaller number first.")

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

    return scrape_clicked, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed

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

def perform_scraping(url, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed_matches, status_container):
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

        result = st.session_state.scraper.scrape_comprehensive(
            url,
            scrape_matches=scrape_matches,
            scrape_stats=scrape_stats,
            scrape_maps_agents=scrape_maps_agents,
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

def display_event_info(event_info):
    """Display event information"""
    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            if 'title' in event_info:
                st.metric("📋 Event Title", event_info['title'])
            if 'dates' in event_info:
                st.metric("📅 Dates", event_info['dates'])

        with col2:
            if 'location' in event_info:
                st.metric("📍 Location", event_info['location'])
            if 'prize_pool' in event_info:
                st.metric("💰 Prize Pool", event_info['prize_pool'])

        if 'description' in event_info:
            st.text_area("📝 Description", event_info['description'], height=100, disabled=True)

        st.text(f"🔗 URL: {event_info['url']}")
        st.text(f"🕒 Scraped: {event_info['scraped_at']}")

def display_matches_data(matches_data):
    """Display matches data with enhanced visualizations"""
    matches = matches_data.get('matches', [])

    if not matches:
        st.warning("No matches data found")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Total Matches", len(matches))

    with col2:
        completed = len([m for m in matches if m.get('status') == 'Completed'])
        st.metric("✅ Completed", completed)

    with col3:
        scheduled = len([m for m in matches if m.get('status') == 'Scheduled'])
        st.metric("⏰ Scheduled", scheduled)

    with col4:
        teams = set()
        for match in matches:
            teams.add(match.get('team1', ''))
            teams.add(match.get('team2', ''))
        teams.discard('')
        st.metric("🏅 Teams", len(teams))

    # Convert to DataFrame for analysis
    matches_df = pd.DataFrame(matches)

    if not matches_df.empty:
        # Matches by stage visualization
        if 'stage' in matches_df.columns:
            st.subheader("📊 Matches by Stage")
            stage_counts = matches_df['stage'].value_counts()

            fig_stages = px.bar(
                x=stage_counts.index,
                y=stage_counts.values,
                title="Number of Matches by Stage",
                labels={'x': 'Stage', 'y': 'Number of Matches'}
            )
            fig_stages.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_stages, use_container_width=True)

        # Team performance analysis for completed matches
        completed_matches = matches_df[matches_df['status'] == 'Completed'].copy()
        if not completed_matches.empty and 'winner' in completed_matches.columns:
            st.subheader("🏆 Team Performance")

            # Calculate wins for each team
            team_wins = {}
            team_matches = {}

            for _, match in completed_matches.iterrows():
                team1, team2 = match.get('team1', ''), match.get('team2', '')
                winner = match.get('winner', '')

                # Initialize teams
                for team in [team1, team2]:
                    if team and team != '':
                        if team not in team_wins:
                            team_wins[team] = 0
                            team_matches[team] = 0
                        team_matches[team] += 1

                # Count wins
                if winner and winner in team_wins:
                    team_wins[winner] += 1

            # Create performance DataFrame
            if team_wins:
                perf_data = []
                for team in team_wins:
                    wins = team_wins[team]
                    total = team_matches[team]
                    win_rate = (wins / total * 100) if total > 0 else 0
                    perf_data.append({
                        'Team': team,
                        'Wins': wins,
                        'Total Matches': total,
                        'Losses': total - wins,
                        'Win Rate (%)': round(win_rate, 1)
                    })

                perf_df = pd.DataFrame(perf_data).sort_values('Win Rate (%)', ascending=False)

                # Display top teams
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**🥇 Top Performing Teams:**")
                    st.dataframe(perf_df.head(10), hide_index=True)

                with col2:
                    # Win rate chart
                    if len(perf_df) > 0:
                        fig_winrate = px.bar(
                            perf_df.head(10),
                            x='Team',
                            y='Win Rate (%)',
                            title="Team Win Rates",
                            color='Win Rate (%)',
                            color_continuous_scale='RdYlGn'
                        )
                        fig_winrate.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_winrate, use_container_width=True)

        # Matches table with filtering
        st.subheader("📋 Matches Table")

        # Add filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status:",
                options=['All'] + list(matches_df['status'].unique()),
                key="matches_status_filter"
            )

        with col2:
            if 'stage' in matches_df.columns:
                stage_filter = st.selectbox(
                    "Filter by Stage:",
                    options=['All'] + list(matches_df['stage'].unique()),
                    key="matches_stage_filter"
                )
            else:
                stage_filter = 'All'

        with col3:
            # Team search
            team_search = st.text_input(
                "Search Team:",
                placeholder="Enter team name...",
                key="matches_team_search"
            )

        # Apply filters
        filtered_df = matches_df.copy()

        if status_filter != 'All':
            filtered_df = filtered_df[filtered_df['status'] == status_filter]

        if stage_filter != 'All' and 'stage' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['stage'] == stage_filter]

        if team_search:
            team_mask = (
                filtered_df['team1'].str.contains(team_search, case=False, na=False) |
                filtered_df['team2'].str.contains(team_search, case=False, na=False)
            )
            filtered_df = filtered_df[team_mask]

        # Display filtered table with all available columns
        display_columns = ['match_id', 'date', 'time', 'team1', 'score', 'team2', 'winner', 'status', 'week', 'stage', 'match_url']
        available_columns = [col for col in display_columns if col in filtered_df.columns]

        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True,
            hide_index=True
        )

        st.info(f"Showing {len(filtered_df)} of {len(matches_df)} matches")

def display_detailed_matches_data(detailed_matches):
    """Display detailed match data in an organized format with enhanced visualizations"""
    if not detailed_matches:
        st.warning("No detailed match data available")
        return

    st.header("🔍 Detailed Match Analysis")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🏆 Matches Analyzed", len(detailed_matches))

    with col2:
        total_maps = sum(len(match.get('maps', [])) for match in detailed_matches)
        st.metric("🗺️ Total Maps", total_maps)

    with col3:
        total_players = 0
        for match in detailed_matches:
            for map_data in match.get('maps', []):
                for team_stats in map_data.get('player_stats', {}).values():
                    total_players += len(team_stats)
        st.metric("👥 Player Records", total_players)

    with col4:
        # Count unique agents across all matches
        unique_agents = set()
        for match in detailed_matches:
            for team_stats in match.get('overall_player_stats', {}).values():
                for player in team_stats:
                    unique_agents.update(player.get('agents', []))
        st.metric("🎭 Unique Agents", len(unique_agents))

    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Match Overview", "🗺️ Map Analysis", "👥 Player Performance", "🎯 Head-to-Head", "📈 Performance Trends"])

    with tab1:
        display_match_overview_tab(detailed_matches)

    with tab2:
        display_map_analysis_tab(detailed_matches)

    with tab3:
        display_player_performance_tab(detailed_matches)

    with tab4:
        display_head_to_head_tab(detailed_matches)

    with tab5:
        display_performance_trends_tab(detailed_matches)

def display_match_overview_tab(detailed_matches):
    """Display match overview information"""
    st.subheader("Match Summary")

    # Create a DataFrame for match overview
    match_overview = []
    for match in detailed_matches:
        event_info = match.get('event_info', {})
        teams = match.get('teams', {})
        team1 = teams.get('team1', {})
        team2 = teams.get('team2', {})

        overview = {
            'Match ID': match.get('match_id'),
            'Event': event_info.get('name', 'N/A'),
            'Stage': event_info.get('stage', 'N/A'),
            'Date': event_info.get('date_utc', 'N/A'),
            'Team 1': team1.get('name', 'N/A'),
            'Team 2': team2.get('name', 'N/A'),
            'Score': f"{team1.get('score_overall', 0)} - {team2.get('score_overall', 0)}",
            'Format': match.get('match_format', 'N/A'),
            'Patch': event_info.get('patch', 'N/A'),
            'Maps Played': len(match.get('maps', [])),
            'Pick/Ban Info': match.get('map_picks_bans_note', 'N/A')[:50] + '...' if len(match.get('map_picks_bans_note', '')) > 50 else match.get('map_picks_bans_note', 'N/A')
        }
        match_overview.append(overview)

    if match_overview:
        df_overview = pd.DataFrame(match_overview)
        st.dataframe(df_overview, use_container_width=True, hide_index=True)

        # Match results visualization
        if len(detailed_matches) > 1:
            st.subheader("📊 Match Results Distribution")

            # Create score difference analysis
            score_diffs = []
            for match in detailed_matches:
                teams = match.get('teams', {})
                team1_score = teams.get('team1', {}).get('score_overall', 0)
                team2_score = teams.get('team2', {}).get('score_overall', 0)
                score_diffs.append(abs(team1_score - team2_score))

            fig_scores = px.histogram(
                x=score_diffs,
                nbins=max(1, len(set(score_diffs))),
                title="Score Difference Distribution",
                labels={'x': 'Score Difference', 'y': 'Number of Matches'}
            )
            st.plotly_chart(fig_scores, use_container_width=True)

def display_map_analysis_tab(detailed_matches):
    """Display detailed map analysis"""
    st.subheader("Map Performance Analysis")

    # Collect all map data
    all_maps_data = []
    for match in detailed_matches:
        match_id = match.get('match_id')
        teams = match.get('teams', {})
        team1_name = teams.get('team1', {}).get('name', 'Team 1')
        team2_name = teams.get('team2', {}).get('name', 'Team 2')

        for map_data in match.get('maps', []):
            map_info = {
                'Match ID': match_id,
                'Map Order': map_data.get('map_order', 0),
                'Map Name': map_data.get('map_name', 'Unknown'),
                'Team 1': team1_name,
                'Team 2': team2_name,
                'Team 1 Score': map_data.get('team1_score_map', 0),
                'Team 2 Score': map_data.get('team2_score_map', 0),
                'Winner': map_data.get('winner_team_name', 'Unknown'),
                'Duration': map_data.get('map_duration', 'N/A'),
                'Picked By': map_data.get('picked_by', 'Unknown')
            }
            all_maps_data.append(map_info)

    if all_maps_data:
        maps_df = pd.DataFrame(all_maps_data)

        # Display maps table
        st.dataframe(maps_df, use_container_width=True, hide_index=True)

        # Map statistics
        col1, col2 = st.columns(2)

        with col1:
            # Map win rates
            if 'Map Name' in maps_df.columns and 'Winner' in maps_df.columns:
                st.subheader("🗺️ Map Performance")
                map_wins = maps_df.groupby(['Map Name', 'Winner']).size().unstack(fill_value=0)

                if not map_wins.empty:
                    # Calculate win percentages
                    map_totals = map_wins.sum(axis=1)
                    map_win_pct = map_wins.div(map_totals, axis=0) * 100

                    # Create stacked bar chart
                    fig_maps = go.Figure()

                    for team in map_win_pct.columns:
                        fig_maps.add_trace(go.Bar(
                            name=team,
                            x=map_win_pct.index,
                            y=map_win_pct[team],
                            text=[f"{val:.1f}%" for val in map_win_pct[team]],
                            textposition='inside'
                        ))

                    fig_maps.update_layout(
                        title='Map Win Rates by Team',
                        barmode='stack',
                        xaxis_title='Map',
                        yaxis_title='Win Rate (%)',
                        yaxis=dict(range=[0, 100])
                    )
                    st.plotly_chart(fig_maps, use_container_width=True)

        with col2:
            # Map pick analysis
            if 'Picked By' in maps_df.columns:
                st.subheader("🎯 Map Picks")
                pick_counts = maps_df['Picked By'].value_counts()

                fig_picks = px.pie(
                    values=pick_counts.values,
                    names=pick_counts.index,
                    title="Map Pick Distribution"
                )
                st.plotly_chart(fig_picks, use_container_width=True)

def display_player_performance_tab(detailed_matches):
    """Display comprehensive player performance analysis"""
    st.subheader("Player Performance Analysis")

    # Collect all player stats from overall stats (aggregated across all maps)
    all_player_stats = []
    for match in detailed_matches:
        match_id = match.get('match_id')
        event_name = match.get('event_info', {}).get('name', 'Unknown Event')

        for team_name, players in match.get('overall_player_stats', {}).items():
            for player in players:
                stats_all = player.get('stats_all_sides', {})

                # Convert stats to numeric for analysis
                player_stat = {
                    'Match ID': match_id,
                    'Event': event_name,
                    'Team': player.get('team_name', team_name),
                    'Player': player.get('player_name', 'Unknown'),
                    'Player ID': player.get('player_id', 'N/A'),
                    'Primary Agent': player.get('agent', 'N/A'),
                    'All Agents': ', '.join(player.get('agents', [])),
                    'Rating': float(stats_all.get('rating', '0')),
                    'ACS': float(stats_all.get('acs', '0')),
                    'Kills': int(stats_all.get('k', '0')),
                    'Deaths': int(stats_all.get('d', '0')),
                    'Assists': int(stats_all.get('a', '0')),
                    'K/D Diff': stats_all.get('kd_diff', '0'),
                    'KAST': stats_all.get('kast', '0%'),
                    'ADR': float(stats_all.get('adr', '0')),
                    'HS%': stats_all.get('hs_percent', '0%'),
                    'First Kills': int(stats_all.get('fk', '0')),
                    'First Deaths': int(stats_all.get('fd', '0')),
                    'FK/FD Diff': stats_all.get('fk_fd_diff', '0')
                }

                # Calculate K/D ratio
                deaths = player_stat['Deaths']
                player_stat['K/D Ratio'] = round(player_stat['Kills'] / deaths if deaths > 0 else player_stat['Kills'], 2)

                all_player_stats.append(player_stat)

    if not all_player_stats:
        st.warning("No player performance data available")
        return

    # Create DataFrame
    players_df = pd.DataFrame(all_player_stats)

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_rating = players_df['Rating'].mean()
        st.metric("📊 Avg Rating", f"{avg_rating:.2f}")

    with col2:
        avg_acs = players_df['ACS'].mean()
        st.metric("🎯 Avg ACS", f"{avg_acs:.0f}")

    with col3:
        avg_kd = players_df['K/D Ratio'].mean()
        st.metric("⚔️ Avg K/D", f"{avg_kd:.2f}")

    with col4:
        total_kills = players_df['Kills'].sum()
        st.metric("💀 Total Kills", f"{total_kills:,}")

    # Top performers section
    st.subheader("🌟 Top Performers")

    perf_tab1, perf_tab2, perf_tab3, perf_tab4 = st.tabs(["🎯 Rating Leaders", "💥 ACS Leaders", "⚔️ K/D Leaders", "🔥 Fraggers"])

    with perf_tab1:
        top_rating = players_df.nlargest(10, 'Rating')[['Player', 'Team', 'Rating', 'ACS', 'Kills', 'Deaths', 'K/D Ratio']]

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(top_rating, hide_index=True)

        with col2:
            fig_rating = px.bar(
                top_rating,
                x='Player',
                y='Rating',
                color='Rating',
                title="Top 10 Players by Rating",
                color_continuous_scale='viridis'
            )
            fig_rating.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_rating, use_container_width=True)

    with perf_tab2:
        top_acs = players_df.nlargest(10, 'ACS')[['Player', 'Team', 'ACS', 'Rating', 'Kills', 'Deaths']]

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(top_acs, hide_index=True)

        with col2:
            fig_acs = px.bar(
                top_acs,
                x='Player',
                y='ACS',
                color='ACS',
                title="Top 10 Players by ACS",
                color_continuous_scale='plasma'
            )
            fig_acs.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_acs, use_container_width=True)

    with perf_tab3:
        top_kd = players_df.nlargest(10, 'K/D Ratio')[['Player', 'Team', 'K/D Ratio', 'Kills', 'Deaths', 'Rating']]

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(top_kd, hide_index=True)

        with col2:
            fig_kd = px.scatter(
                players_df.head(20),
                x='Kills',
                y='Deaths',
                size='K/D Ratio',
                color='Rating',
                hover_data=['Player', 'Team'],
                title="Kills vs Deaths (Size = K/D Ratio, Color = Rating)",
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_kd, use_container_width=True)

    with perf_tab4:
        top_kills = players_df.nlargest(10, 'Kills')[['Player', 'Team', 'Kills', 'Deaths', 'K/D Ratio', 'ACS']]

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(top_kills, hide_index=True)

        with col2:
            fig_kills = px.histogram(
                players_df,
                x='Kills',
                nbins=15,
                title="Distribution of Kills",
                labels={'count': 'Number of Players'}
            )
            st.plotly_chart(fig_kills, use_container_width=True)

    # Team comparison
    st.subheader("🏅 Team Performance Comparison")

    if 'Team' in players_df.columns:
        team_stats = players_df.groupby('Team').agg({
            'Rating': 'mean',
            'ACS': 'mean',
            'K/D Ratio': 'mean',
            'Kills': 'sum',
            'Deaths': 'sum',
            'ADR': 'mean'
        }).round(2)

        team_stats['Total Players'] = players_df.groupby('Team').size()
        team_stats = team_stats.sort_values('Rating', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**📊 Team Averages:**")
            st.dataframe(team_stats, use_container_width=True)

        with col2:
            # Team rating comparison
            fig_team = px.bar(
                team_stats.reset_index(),
                x='Team',
                y='Rating',
                title="Average Team Rating",
                color='Rating',
                color_continuous_scale='viridis'
            )
            fig_team.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_team, use_container_width=True)

    # Full player stats table with search and filters
    st.subheader("🔍 Complete Player Statistics")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        player_search = st.text_input(
            "Search Player:",
            placeholder="Enter player name...",
            key="detailed_player_search"
        )

    with col2:
        team_filter = st.selectbox(
            "Filter by Team:",
            options=['All'] + sorted(players_df['Team'].unique().tolist()),
            key="detailed_team_filter"
        )

    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            options=['Rating', 'ACS', 'Kills', 'K/D Ratio', 'ADR'],
            key="detailed_sort"
        )

    # Apply filters
    filtered_df = players_df.copy()

    if player_search:
        filtered_df = filtered_df[
            filtered_df['Player'].str.contains(player_search, case=False, na=False)
        ]

    if team_filter != 'All':
        filtered_df = filtered_df[filtered_df['Team'] == team_filter]

    if sort_by:
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)

    # Display table
    display_cols = [
        'Player', 'Team', 'Primary Agent', 'Rating', 'ACS', 'Kills', 'Deaths', 'K/D Ratio',
        'Assists', 'KAST', 'ADR', 'HS%', 'First Kills', 'First Deaths'
    ]

    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.info(f"Showing {len(filtered_df)} of {len(players_df)} player records")

def display_head_to_head_tab(detailed_matches):
    """Display head-to-head team analysis"""
    st.subheader("🎯 Head-to-Head Analysis")

    if len(detailed_matches) < 2:
        st.info("Need at least 2 matches for meaningful head-to-head analysis")
        return

    # Collect team matchups
    team_matchups = {}
    for match in detailed_matches:
        teams = match.get('teams', {})
        team1 = teams.get('team1', {}).get('name', 'Team 1')
        team2 = teams.get('team2', {}).get('name', 'Team 2')
        team1_score = teams.get('team1', {}).get('score_overall', 0)
        team2_score = teams.get('team2', {}).get('score_overall', 0)

        # Create matchup key (sorted to avoid duplicates)
        matchup = tuple(sorted([team1, team2]))

        if matchup not in team_matchups:
            team_matchups[matchup] = {
                'matches': [],
                'team1_wins': 0,
                'team2_wins': 0,
                'total_maps': 0
            }

        # Determine winner
        winner = team1 if team1_score > team2_score else team2

        match_info = {
            'match_id': match.get('match_id'),
            'team1': team1,
            'team2': team2,
            'score': f"{team1_score}-{team2_score}",
            'winner': winner,
            'maps_played': len(match.get('maps', []))
        }

        team_matchups[matchup]['matches'].append(match_info)
        team_matchups[matchup]['total_maps'] += len(match.get('maps', []))

        if winner == matchup[0]:
            team_matchups[matchup]['team1_wins'] += 1
        else:
            team_matchups[matchup]['team2_wins'] += 1

    # Display matchup analysis
    for matchup, data in team_matchups.items():
        if len(data['matches']) > 1:  # Only show if teams played multiple times
            team1, team2 = matchup

            with st.expander(f"{team1} vs {team2} ({len(data['matches'])} matches)"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(f"{team1} Wins", data['team1_wins'])

                with col2:
                    st.metric(f"{team2} Wins", data['team2_wins'])

                with col3:
                    st.metric("Total Maps", data['total_maps'])

                # Match history
                st.write("**Match History:**")
                matches_df = pd.DataFrame(data['matches'])
                st.dataframe(matches_df, hide_index=True)

                # Win rate visualization
                if data['team1_wins'] + data['team2_wins'] > 0:
                    win_data = {
                        'Team': [team1, team2],
                        'Wins': [data['team1_wins'], data['team2_wins']]
                    }

                    fig_wins = px.pie(
                        win_data,
                        values='Wins',
                        names='Team',
                        title=f"{team1} vs {team2} Win Distribution"
                    )
                    st.plotly_chart(fig_wins, use_container_width=True)

def display_performance_trends_tab(detailed_matches):
    """Display performance trends and agent analysis"""
    st.subheader("📈 Performance Trends & Agent Analysis")

    # Agent usage analysis
    st.subheader("🎭 Agent Usage Analysis")

    # Collect agent data from overall stats
    agent_usage = {}
    agent_performance = {}

    for match in detailed_matches:
        for team_name, players in match.get('overall_player_stats', {}).items():
            for player in players:
                agents = player.get('agents', [])
                primary_agent = player.get('agent', 'Unknown')
                rating = float(player.get('stats_all_sides', {}).get('rating', '0'))
                acs = float(player.get('stats_all_sides', {}).get('acs', '0'))

                # Count agent usage
                for agent in agents:
                    if agent not in agent_usage:
                        agent_usage[agent] = 0
                        agent_performance[agent] = {'ratings': [], 'acs': []}

                    agent_usage[agent] += 1
                    agent_performance[agent]['ratings'].append(rating)
                    agent_performance[agent]['acs'].append(acs)

    if agent_usage:
        # Agent usage distribution
        col1, col2 = st.columns(2)

        with col1:
            st.write("**🎮 Agent Pick Rates:**")
            usage_df = pd.DataFrame(list(agent_usage.items()), columns=['Agent', 'Times Picked'])
            usage_df = usage_df.sort_values('Times Picked', ascending=False)

            fig_usage = px.bar(
                usage_df.head(10),
                x='Agent',
                y='Times Picked',
                title="Top 10 Most Picked Agents",
                color='Times Picked',
                color_continuous_scale='viridis'
            )
            fig_usage.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_usage, use_container_width=True)

        with col2:
            st.write("**⭐ Agent Performance:**")
            # Calculate average performance per agent
            perf_data = []
            for agent, data in agent_performance.items():
                if len(data['ratings']) > 0:
                    avg_rating = sum(data['ratings']) / len(data['ratings'])
                    avg_acs = sum(data['acs']) / len(data['acs'])
                    perf_data.append({
                        'Agent': agent,
                        'Avg Rating': round(avg_rating, 2),
                        'Avg ACS': round(avg_acs, 0),
                        'Times Played': len(data['ratings'])
                    })

            if perf_data:
                perf_df = pd.DataFrame(perf_data)
                perf_df = perf_df.sort_values('Avg Rating', ascending=False)

                fig_perf = px.scatter(
                    perf_df,
                    x='Avg ACS',
                    y='Avg Rating',
                    size='Times Played',
                    hover_data=['Agent'],
                    title="Agent Performance: Rating vs ACS",
                    color='Avg Rating',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_perf, use_container_width=True)

        # Detailed agent stats table
        st.write("**📊 Detailed Agent Statistics:**")
        if perf_data:
            perf_df_display = pd.DataFrame(perf_data).sort_values('Times Played', ascending=False)
            st.dataframe(perf_df_display, hide_index=True)

    # Map performance trends
    st.subheader("🗺️ Map Performance Trends")

    map_stats = {}
    for match in detailed_matches:
        for map_data in match.get('maps', []):
            map_name = map_data.get('map_name', 'Unknown')
            duration = map_data.get('map_duration', 'N/A')
            team1_score = map_data.get('team1_score_map', 0)
            team2_score = map_data.get('team2_score_map', 0)

            if map_name not in map_stats:
                map_stats[map_name] = {
                    'played': 0,
                    'total_rounds': 0,
                    'durations': [],
                    'close_games': 0  # Games decided by 3 rounds or less
                }

            map_stats[map_name]['played'] += 1
            map_stats[map_name]['total_rounds'] += team1_score + team2_score

            if duration != 'N/A':
                map_stats[map_name]['durations'].append(duration)

            # Check if it was a close game
            if abs(team1_score - team2_score) <= 3:
                map_stats[map_name]['close_games'] += 1

    if map_stats:
        map_analysis = []
        for map_name, stats in map_stats.items():
            avg_rounds = stats['total_rounds'] / stats['played'] if stats['played'] > 0 else 0
            close_game_rate = (stats['close_games'] / stats['played'] * 100) if stats['played'] > 0 else 0

            map_analysis.append({
                'Map': map_name,
                'Times Played': stats['played'],
                'Avg Total Rounds': round(avg_rounds, 1),
                'Close Games (%)': round(close_game_rate, 1)
            })

        map_df = pd.DataFrame(map_analysis).sort_values('Times Played', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(map_df, hide_index=True)

        with col2:
            fig_maps = px.bar(
                map_df,
                x='Map',
                y='Times Played',
                title="Map Play Frequency",
                color='Close Games (%)',
                color_continuous_scale='RdYlBu'
            )
            fig_maps.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_maps, use_container_width=True)

def display_stats_data(stats_data):
    """Display player statistics data with enhanced visualizations"""
    player_stats = stats_data.get('player_stats', [])

    if not player_stats:
        st.warning("No player statistics found")
        return

    # Convert to DataFrame
    stats_df = pd.DataFrame(player_stats)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👥 Total Players", len(player_stats))

    with col2:
        unique_teams = len(set([p.get('team', '') for p in player_stats if p.get('team')]))
        st.metric("🏅 Teams", unique_teams)

    with col3:
        # Average ACS
        if 'acs' in stats_df.columns:
            avg_acs = pd.to_numeric(stats_df['acs'], errors='coerce').mean()
            st.metric("📊 Avg ACS", f"{avg_acs:.1f}" if not pd.isna(avg_acs) else "N/A")
        else:
            st.metric("📊 Data Points", len(player_stats))

    with col4:
        # Average K/D
        if 'kd_ratio' in stats_df.columns:
            kd_numeric = pd.to_numeric(stats_df['kd_ratio'], errors='coerce')
            avg_kd = kd_numeric.mean()
            st.metric("⚔️ Avg K/D", f"{avg_kd:.2f}" if not pd.isna(avg_kd) else "N/A")
        else:
            st.metric("📈 Records", len(player_stats))

    # Convert numeric columns for analysis
    numeric_cols = ['rating', 'acs', 'kills', 'deaths', 'assists', 'adr', 'kd_ratio']
    for col in numeric_cols:
        if col in stats_df.columns:
            stats_df[col] = pd.to_numeric(stats_df[col], errors='coerce')

    # Top performers section
    st.subheader("🌟 Top Performers")

    # Create tabs for different metrics
    perf_tab1, perf_tab2, perf_tab3, perf_tab4 = st.tabs(["🎯 ACS Leaders", "⚔️ K/D Leaders", "🔥 Fraggers", "🎖️ Rating Leaders"])

    with perf_tab1:
        if 'acs' in stats_df.columns:
            top_acs = stats_df.nlargest(15, 'acs')[['player', 'team', 'acs', 'kills', 'deaths', 'kd_ratio']]

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(top_acs.head(10), hide_index=True)

            with col2:
                # ACS distribution chart
                fig_acs = px.bar(
                    top_acs.head(10),
                    x='player',
                    y='acs',
                    title="Top 10 Players by ACS",
                    color='acs',
                    color_continuous_scale='viridis'
                )
                fig_acs.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_acs, use_container_width=True)

    with perf_tab2:
        if 'kd_ratio' in stats_df.columns:
            # Filter out infinite values for display
            kd_filtered = stats_df[stats_df['kd_ratio'] != float('inf')].copy()
            top_kd = kd_filtered.nlargest(15, 'kd_ratio')[['player', 'team', 'kd_ratio', 'kills', 'deaths', 'acs']]

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(top_kd.head(10), hide_index=True)

            with col2:
                # K/D scatter plot
                if len(top_kd) > 0:
                    fig_kd = px.scatter(
                        top_kd.head(15),
                        x='kills',
                        y='deaths',
                        size='kd_ratio',
                        color='kd_ratio',
                        hover_data=['player', 'team'],
                        title="Kills vs Deaths (Size = K/D Ratio)",
                        color_continuous_scale='RdYlGn'
                    )
                    st.plotly_chart(fig_kd, use_container_width=True)

    with perf_tab3:
        if 'kills' in stats_df.columns:
            top_kills = stats_df.nlargest(15, 'kills')[['player', 'team', 'kills', 'deaths', 'acs', 'kd_ratio']]

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(top_kills.head(10), hide_index=True)

            with col2:
                # Kills distribution
                fig_kills = px.histogram(
                    stats_df,
                    x='kills',
                    nbins=20,
                    title="Distribution of Kills",
                    labels={'count': 'Number of Players'}
                )
                st.plotly_chart(fig_kills, use_container_width=True)

    with perf_tab4:
        if 'rating' in stats_df.columns:
            top_rating = stats_df.nlargest(15, 'rating')[['player', 'team', 'rating', 'acs', 'kills', 'kd_ratio']]

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(top_rating.head(10), hide_index=True)

            with col2:
                # Rating vs ACS correlation
                if len(stats_df) > 0:
                    fig_rating = px.scatter(
                        stats_df.head(50),
                        x='rating',
                        y='acs',
                        hover_data=['player', 'team'],
                        title="Rating vs ACS Correlation",
                        trendline="ols"
                    )
                    st.plotly_chart(fig_rating, use_container_width=True)

    # Team analysis
    if 'team' in stats_df.columns and stats_df['team'].notna().any():
        st.subheader("🏅 Team Analysis")

        # Calculate team averages
        team_stats = stats_df.groupby('team').agg({
            'acs': 'mean',
            'kd_ratio': 'mean',
            'kills': 'mean',
            'rating': 'mean'
        }).round(2)

        team_stats['player_count'] = stats_df.groupby('team').size()
        team_stats = team_stats.sort_values('acs', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**📊 Team Performance Summary:**")
            st.dataframe(team_stats, use_container_width=True)

        with col2:
            # Team ACS comparison
            if len(team_stats) > 0:
                fig_team = px.bar(
                    team_stats.head(10),
                    y=team_stats.head(10).index,
                    x='acs',
                    orientation='h',
                    title="Team Average ACS",
                    color='acs',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig_team, use_container_width=True)

    # Player search and filtering
    st.subheader("🔍 Player Search & Filter")

    col1, col2, col3 = st.columns(3)

    with col1:
        player_search = st.text_input(
            "Search Player:",
            placeholder="Enter player name...",
            key="player_search"
        )

    with col2:
        if 'team' in stats_df.columns:
            team_filter = st.selectbox(
                "Filter by Team:",
                options=['All'] + sorted(stats_df['team'].dropna().unique().tolist()),
                key="player_team_filter"
            )
        else:
            team_filter = 'All'

    with col3:
        # Sort options
        sort_options = ['acs', 'rating', 'kills', 'kd_ratio', 'adr']
        available_sort = [opt for opt in sort_options if opt in stats_df.columns]

        if available_sort:
            sort_by = st.selectbox(
                "Sort by:",
                options=available_sort,
                key="player_sort"
            )
        else:
            sort_by = None

    # Apply filters
    filtered_stats = stats_df.copy()

    if player_search:
        filtered_stats = filtered_stats[
            filtered_stats['player'].str.contains(player_search, case=False, na=False)
        ]

    if team_filter != 'All' and 'team' in filtered_stats.columns:
        filtered_stats = filtered_stats[filtered_stats['team'] == team_filter]

    if sort_by and sort_by in filtered_stats.columns:
        filtered_stats = filtered_stats.sort_values(sort_by, ascending=False)

    # Full stats table
    st.subheader("📊 Player Statistics Table")
    display_cols = [
        'player_id', 'player', 'team', 'agents_display', 'rating', 'acs', 'kd_ratio', 'kast', 'adr',
        'kills', 'deaths', 'assists', 'rounds', 'kpr', 'apr',
        'fkpr', 'fdpr', 'hs_percent', 'cl_percent', 'clutches',
        'k_max', 'first_kills', 'first_deaths', 'agents_count'
    ]
    available_cols = [col for col in display_cols if col in filtered_stats.columns]

    st.dataframe(
        filtered_stats[available_cols],
        use_container_width=True,
        hide_index=True
    )

    st.info(f"Showing {len(filtered_stats)} of {len(stats_df)} players")

def display_maps_agents_data(maps_agents_data):
    """Display maps and agents data with visualizations"""
    if not maps_agents_data:
        st.warning("No maps and agents data available")
        return

    st.header("🎭 Maps & Agents Analysis")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🗺️ Map Statistics", "🎮 Agent Utilization"])
    
    with tab1:
        st.subheader("Map Statistics")
        if 'maps' in maps_agents_data:
            maps_df = pd.DataFrame(maps_agents_data['maps'])
            if not maps_df.empty:
                # Remove scraped_at column if it exists
                if 'scraped_at' in maps_df.columns:
                    maps_df = maps_df.drop('scraped_at', axis=1)
                st.dataframe(maps_df, use_container_width=True)
                
                # Create map win rate visualization
                if 'map_name' in maps_df.columns and 'attack_win_percent' in maps_df.columns:
                    # Convert percentages to numeric values
                    maps_df['attack_win'] = pd.to_numeric(maps_df['attack_win_percent'].str.replace('%', ''), errors='coerce')
                    maps_df['defense_win'] = pd.to_numeric(maps_df['defense_win_percent'].str.replace('%', ''), errors='coerce')
                    
                    # Create the visualization
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='Attack Win %',
                        x=maps_df['map_name'],
                        y=maps_df['attack_win']
                    ))
                    fig.add_trace(go.Bar(
                        name='Defense Win %',
                        x=maps_df['map_name'],
                        y=maps_df['defense_win']
                    ))
                    fig.update_layout(
                        title='Map Win Rates by Side',
                        barmode='group',
                        xaxis_title='Map',
                        yaxis_title='Win Rate (%)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Agent Utilization")
        if 'agents' in maps_agents_data:
            agents_df = pd.DataFrame(maps_agents_data['agents'])
            if not agents_df.empty:
                # Remove scraped_at column if it exists
                if 'scraped_at' in agents_df.columns:
                    agents_df = agents_df.drop('scraped_at', axis=1)
                
                # Display total utilization
                st.markdown("### Total Agent Utilization")
                total_util_df = agents_df[['agent_name', 'total_utilization_percent']].copy()
                total_util_df = total_util_df.sort_values('total_utilization_percent', ascending=False)
                st.dataframe(total_util_df, use_container_width=True)
                
                # Create total utilization visualization
                fig = px.bar(total_util_df, 
                           x='agent_name', 
                           y='total_utilization_percent',
                           title='Total Agent Utilization',
                           labels={'agent_name': 'Agent', 'total_utilization_percent': 'Utilization (%)'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Display map-specific utilization
                st.markdown("### Map-Specific Agent Utilization")
                for _, agent in agents_df.iterrows():
                    with st.expander(f"{agent['agent_name']} - {agent['total_utilization_percent']}% Total"):
                        if agent.get('map_utilizations'):
                            map_utils = pd.DataFrame(agent['map_utilizations'])
                            map_utils = map_utils.sort_values('utilization_percent', ascending=False)
                            
                            # Create map-specific visualization
                            fig = px.bar(map_utils,
                                       x='map',
                                       y='utilization_percent',
                                       title=f"{agent['agent_name']} Map Utilization",
                                       labels={'map': 'Map', 'utilization_percent': 'Utilization (%)'})
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Display the data table
                            st.dataframe(map_utils, use_container_width=True)

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

                    # Flatten overall stats for display
                    all_overall_stats = []
                    for team_name, players in overall_stats.items():
                        for player in players:
                            # Flatten the nested stats structure
                            flat_player = {
                                'Team': player.get('team_name', team_name),
                                'Player': player.get('player_name', 'Unknown'),
                                'Player ID': player.get('player_id', 'N/A'),
                                'Primary Agent': player.get('agent', 'N/A'),
                                'All Agents': ', '.join(player.get('agents', [])),
                            }

                            # Add all sides stats
                            stats_all = player.get('stats_all_sides', {})
                            for key, value in stats_all.items():
                                flat_player[f'All_{key}'] = value

                            # Add attack stats
                            stats_attack = player.get('stats_attack', {})
                            for key, value in stats_attack.items():
                                flat_player[f'Attack_{key}'] = value

                            # Add defense stats
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

                        # Flatten map player stats
                        map_player_stats = []
                        for team_name, players in map_data.get('player_stats', {}).items():
                            for player in players:
                                flat_player = {
                                    'Team': player.get('team_name', team_name),
                                    'Player': player.get('player_name', 'Unknown'),
                                    'Player ID': player.get('player_id', 'N/A'),
                                    'Agent': player.get('agent', 'N/A'),
                                }

                                # Add all sides stats
                                stats_all = player.get('stats_all_sides', {})
                                for key, value in stats_all.items():
                                    flat_player[f'All_{key}'] = value

                                # Add attack stats
                                stats_attack = player.get('stats_attack', {})
                                for key, value in stats_attack.items():
                                    flat_player[f'Attack_{key}'] = value

                                # Add defense stats
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

def display_database_section():
    """Display database management section"""
    st.header("🗄️ Database Management")

    # Database stats
    db_stats = st.session_state.db.get_database_stats()
    db_size = st.session_state.db.get_database_size()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Events", db_stats.get('total_events', 0))

    with col2:
        st.metric("🏆 Matches", db_stats.get('total_matches', 0))

    with col3:
        st.metric("👥 Players", db_stats.get('unique_players', 0))

    with col4:
        st.metric("💾 DB Size", db_size)

    # Save to database section
    if st.session_state.scraped_data:
        st.subheader("💾 Save Current Data to Database")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗄️ Save to Database", type="primary"):
                try:
                    event_id = st.session_state.db.save_comprehensive_data(st.session_state.scraped_data)
                    st.success(f"✅ Data saved to database! Event ID: {event_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving to database: {e}")

        with col2:
            st.info("💡 **Tip**: Save your scraped data to the database for persistent storage and easy retrieval later.")

    # View saved events
    st.subheader("📋 Saved Events")

    try:
        events_df = st.session_state.db.get_events_list()

        if not events_df.empty:
            # Display events table
            st.dataframe(
                events_df[['event_id', 'title', 'dates', 'location', 'scraped_at']],
                use_container_width=True,
                hide_index=True
            )

            # Event management
            col1, col2, col3 = st.columns(3)

            with col1:
                selected_event = st.selectbox(
                    "Select Event to View:",
                    options=events_df['event_id'].tolist(),
                    format_func=lambda x: f"{x} - {events_df[events_df['event_id']==x]['title'].iloc[0] if len(events_df[events_df['event_id']==x]) > 0 else 'Unknown'}",
                    key="db_event_select"
                )

            with col2:
                if st.button("👁️ View Event Data"):
                    if selected_event:
                        try:
                            event_data = st.session_state.db.get_event_data(selected_event)
                            st.session_state.db_event_data = event_data
                            st.session_state.show_db_event = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading event data: {e}")

            with col3:
                if st.button("🗑️ Delete Event", type="secondary"):
                    if selected_event:
                        if st.session_state.db.delete_event(selected_event):
                            st.success(f"Event {selected_event} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete event")
        else:
            st.info("No events saved in database yet. Scrape some data and save it to get started!")

    except Exception as e:
        st.error(f"Error accessing database: {e}")

def display_database_event_data():
    """Display event data from database"""
    if not hasattr(st.session_state, 'db_event_data') or not st.session_state.get('show_db_event', False):
        return

    st.header("📊 Database Event Data")

    event_data = st.session_state.db_event_data

    # Close button
    if st.button("❌ Close Database View"):
        st.session_state.show_db_event = False
        st.rerun()

    # Create tabs for database data
    tab1, tab2, tab3, tab4 = st.tabs(["ℹ️ Event Info", "🏆 Matches", "📊 Player Stats", "🎭 Agent Usage"])

    with tab1:
        if not event_data['event_info'].empty:
            event_info = event_data['event_info'].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📋 Title", event_info.get('title', 'N/A'))
                st.metric("📅 Dates", event_info.get('dates', 'N/A'))

            with col2:
                st.metric("📍 Location", event_info.get('location', 'N/A'))
                st.metric("💰 Prize Pool", event_info.get('prize_pool', 'N/A'))
        else:
            st.warning("No event information found")

    with tab2:
        if not event_data['matches'].empty:
            matches_df = event_data['matches']

            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Matches", len(matches_df))
            with col2:
                completed = len(matches_df[matches_df['status'] == 'Completed'])
                st.metric("✅ Completed", completed)
            with col3:
                scheduled = len(matches_df[matches_df['status'] == 'Scheduled'])
                st.metric("⏰ Scheduled", scheduled)

            # Matches table
            display_cols = ['match_id', 'date', 'time', 'team1', 'score', 'team2', 'winner', 'status', 'week', 'stage']
            available_cols = [col for col in display_cols if col in matches_df.columns]

            st.dataframe(
                matches_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No matches data found")

    with tab3:
        if not event_data['player_stats'].empty:
            stats_df = event_data['player_stats']

            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total Players", len(stats_df))
            with col2:
                unique_teams = stats_df['team'].nunique()
                st.metric("🏅 Teams", unique_teams)
            with col3:
                avg_acs = stats_df['acs'].mean() if 'acs' in stats_df.columns else 0
                st.metric("📊 Avg ACS", f"{avg_acs:.1f}")

            # Top performers
            if 'acs' in stats_df.columns:
                top_players = stats_df.nlargest(10, 'acs')[['player', 'team', 'acs', 'kills', 'deaths', 'kd_ratio']]
                st.subheader("🌟 Top Performers")
                st.dataframe(top_players, hide_index=True)

            # Full table
            st.subheader("📊 All Player Statistics")
            display_cols = ['player', 'team', 'rating', 'acs', 'kills', 'deaths', 'kd_ratio']
            available_cols = [col for col in display_cols if col in stats_df.columns]

            st.dataframe(
                stats_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No player statistics found")

    with tab4:
        if not event_data['agent_usage'].empty:
            agents_df = event_data['agent_usage']

            # Summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎭 Total Agents", len(agents_df))
            with col2:
                total_usage = agents_df['usage_count'].sum() if 'usage_count' in agents_df.columns else 0
                st.metric("📊 Total Picks", total_usage)

            # Agent usage chart
            if 'usage_percentage' in agents_df.columns:
                # Clean percentage data
                agents_df['usage_pct_clean'] = pd.to_numeric(
                    agents_df['usage_percentage'].str.replace('%', ''),
                    errors='coerce'
                )

                fig = px.bar(
                    agents_df.head(10),
                    x='agent',
                    y='usage_pct_clean',
                    title='Agent Usage Distribution',
                    labels={'usage_pct_clean': 'Usage Percentage (%)', 'agent': 'Agent'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # Full table
            st.subheader("🎭 Agent Usage Statistics")
            display_cols = ['agent', 'usage_count', 'usage_percentage', 'win_rate']
            available_cols = [col for col in display_cols if col in agents_df.columns]

            st.dataframe(
                agents_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No agent usage data found")

def display_save_options():
    """Display 3 main save options as requested"""
    if not st.session_state.scraped_data:
        return

    st.header("💾 Step 3: Save Your Data")

    st.markdown("Choose how you want to save the scraped data:")

    # 3 main options in columns
    col1, col2, col3 = st.columns(3)

    data = st.session_state.scraped_data

    # Option 1: Save to Database
    with col1:
        st.subheader("🗄️ Save to Database")
        st.markdown("Save all data to SQLite3 database for persistent storage")

        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            try:
                with st.spinner("Saving to database..."):
                    event_id = st.session_state.db.save_comprehensive_data(st.session_state.scraped_data)

                    # Also save detailed matches if available
                    detailed_matches = st.session_state.scraped_data.get('detailed_matches', [])
                    if detailed_matches:
                        detailed_count = st.session_state.db.save_detailed_matches(detailed_matches, event_id)
                        st.success(f"✅ Data saved to database! Event ID: {event_id}")
                        st.info(f"📊 Saved {detailed_count} detailed matches")
                    else:
                        st.success(f"✅ Data saved to database! Event ID: {event_id}")

                st.balloons()
            except Exception as e:
                st.error(f"❌ Error saving to database: {e}")

    # Option 2: Download Complete JSON
    with col2:
        st.subheader("📄 Download JSON")
        st.markdown("Download all scraped data in a single JSON file")

        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📄 Download Complete JSON",
            data=json_data,
            file_name=f"vlr_complete_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="Download all scraped data in JSON format"
        )

    # Option 3: Download CSV Files
    with col3:
        st.subheader("📊 Download CSV")
        st.markdown("Download data as separate CSV files by category")

        # Create ZIP with all available CSV files - ONE CLICK DOWNLOAD
        # Prepare all CSV files for ZIP
        csv_files = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Add matches CSV if available
        if data.get('matches_data', {}).get('matches'):
            matches_df = pd.DataFrame(data['matches_data']['matches'])
            csv_files[f"vlr_matches_{timestamp}.csv"] = matches_df.to_csv(index=False)

        # Add player stats CSV if available
        if data.get('stats_data', {}).get('player_stats'):
            stats_df = pd.DataFrame(data['stats_data']['player_stats'])
            csv_files[f"vlr_player_stats_{timestamp}.csv"] = stats_df.to_csv(index=False)

        # Add agent utilization CSV if available
        if data.get('maps_agents_data', {}).get('agents'):
            agents_df = pd.DataFrame(data['maps_agents_data']['agents'])
            csv_files[f"vlr_agent_utilization_{timestamp}.csv"] = agents_df.to_csv(index=False)

        # Add maps CSV if available
        if data.get('maps_agents_data', {}).get('maps'):
            maps_df = pd.DataFrame(data['maps_agents_data']['maps'])
            csv_files[f"vlr_maps_{timestamp}.csv"] = maps_df.to_csv(index=False)

        # Add detailed data if available - CONSOLIDATED FORMAT
        if data.get('detailed_matches'):
            detailed_matches = data['detailed_matches']

            # 1. Detailed matches CSV (match-level data)
            detailed_matches_data = []
            for match in detailed_matches:
                event_info = match.get('event_info', {})
                teams = match.get('teams', {})
                team1 = teams.get('team1', {})
                team2 = teams.get('team2', {})

                # Add match info
                match_record = {
                    'Match ID': match.get('match_id', ''),
                    'Event': event_info.get('name', ''),
                    'Stage': event_info.get('stage', ''),
                    'Date UTC': event_info.get('date_utc', ''),
                    'Patch': event_info.get('patch', ''),
                    'Team 1': team1.get('name', ''),
                    'Team 2': team2.get('name', ''),
                    'Team 1 Score': team1.get('score_overall', ''),
                    'Team 2 Score': team2.get('score_overall', ''),
                    'Format': match.get('match_format', ''),
                    'Pick/Ban Info': match.get('map_picks_bans_note', ''),
                    'Match URL': match.get('match_url', ''),
                    'Scraped At': match.get('scraped_at', '')
                }

                # Add map details to the same record
                maps_info = []
                for map_data in match.get('maps', []):
                    map_info = f"{map_data.get('map_name', '')} ({map_data.get('team1_score_map', '')}-{map_data.get('team2_score_map', '')})"
                    maps_info.append(map_info)

                match_record['Maps Played'] = ' | '.join(maps_info)
                detailed_matches_data.append(match_record)

            if detailed_matches_data:
                detailed_df = pd.DataFrame(detailed_matches_data)
                csv_files[f"vlr_detailed_matches_{timestamp}.csv"] = detailed_df.to_csv(index=False)

            # 2. Detailed player stats CSV (using the preferred format)
            detailed_player_data = []
            for match in detailed_matches:
                match_id = match.get('match_id', '')
                event_name = match.get('event_info', {}).get('name', '')

                # Overall player stats (match-level)
                for team_name, players in match.get('overall_player_stats', {}).items():
                    for player in players:
                        stats_all = player.get('stats_all_sides', {})
                        stats_attack = player.get('stats_attack', {})
                        stats_defense = player.get('stats_defense', {})

                        # Get all agents for this player across all maps
                        all_agents = player.get('agents', [])
                        primary_agent = player.get('agent', '')
                        all_agents_str = ', '.join(all_agents) if all_agents else primary_agent

                        player_record = {
                            'Match ID': match_id,
                            'Event': event_name,
                            'Map': 'Overall',
                            'Team': team_name,
                            'Player': player.get('player_name', ''),
                            'Player ID': player.get('player_id', ''),
                            'Primary Agent': primary_agent,
                            'All Agents': all_agents_str,

                            # All sides stats
                            'Rating': stats_all.get('rating', ''),
                            'ACS': stats_all.get('acs', ''),
                            'Kills': stats_all.get('k', ''),
                            'Deaths': stats_all.get('d', ''),
                            'Assists': stats_all.get('a', ''),
                            'K/D Diff': stats_all.get('kd_diff', ''),
                            'KAST': stats_all.get('kast', ''),
                            'ADR': stats_all.get('adr', ''),
                            'HS%': stats_all.get('hs_percent', ''),
                            'First Kills': stats_all.get('fk', ''),
                            'First Deaths': stats_all.get('fd', ''),
                            'FK/FD Diff': stats_all.get('fk_fd_diff', ''),

                            # Attack stats
                            'Attack Rating': stats_attack.get('rating', ''),
                            'Attack ACS': stats_attack.get('acs', ''),
                            'Attack Kills': stats_attack.get('k', ''),
                            'Attack Deaths': stats_attack.get('d', ''),
                            'Attack Assists': stats_attack.get('a', ''),
                            'Attack KAST': stats_attack.get('kast', ''),
                            'Attack ADR': stats_attack.get('adr', ''),

                            # Defense stats
                            'Defense Rating': stats_defense.get('rating', ''),
                            'Defense ACS': stats_defense.get('acs', ''),
                            'Defense Kills': stats_defense.get('k', ''),
                            'Defense Deaths': stats_defense.get('d', ''),
                            'Defense Assists': stats_defense.get('a', ''),
                            'Defense KAST': stats_defense.get('kast', ''),
                            'Defense ADR': stats_defense.get('adr', ''),
                        }
                        detailed_player_data.append(player_record)

                # Map-by-map player stats
                for map_data in match.get('maps', []):
                    map_name = map_data.get('map_name', '')
                    for team_name, players in map_data.get('player_stats', {}).items():
                        for player in players:
                            stats_all = player.get('stats_all_sides', {})
                            stats_attack = player.get('stats_attack', {})
                            stats_defense = player.get('stats_defense', {})

                            agent = player.get('agent', '')

                            player_record = {
                                'Match ID': match_id,
                                'Event': event_name,
                                'Map': map_name,
                                'Team': team_name,
                                'Player': player.get('player_name', ''),
                                'Player ID': player.get('player_id', ''),
                                'Primary Agent': agent,
                                'All Agents': agent,  # Single agent for individual map

                                # All sides stats
                                'Rating': stats_all.get('rating', ''),
                                'ACS': stats_all.get('acs', ''),
                                'Kills': stats_all.get('k', ''),
                                'Deaths': stats_all.get('d', ''),
                                'Assists': stats_all.get('a', ''),
                                'K/D Diff': stats_all.get('kd_diff', ''),
                                'KAST': stats_all.get('kast', ''),
                                'ADR': stats_all.get('adr', ''),
                                'HS%': stats_all.get('hs_percent', ''),
                                'First Kills': stats_all.get('fk', ''),
                                'First Deaths': stats_all.get('fd', ''),
                                'FK/FD Diff': stats_all.get('fk_fd_diff', ''),

                                # Attack stats
                                'Attack Rating': stats_attack.get('rating', ''),
                                'Attack ACS': stats_attack.get('acs', ''),
                                'Attack Kills': stats_attack.get('k', ''),
                                'Attack Deaths': stats_attack.get('d', ''),
                                'Attack Assists': stats_attack.get('a', ''),
                                'Attack KAST': stats_attack.get('kast', ''),
                                'Attack ADR': stats_attack.get('adr', ''),

                                # Defense stats
                                'Defense Rating': stats_defense.get('rating', ''),
                                'Defense ACS': stats_defense.get('acs', ''),
                                'Defense Kills': stats_defense.get('k', ''),
                                'Defense Deaths': stats_defense.get('d', ''),
                                'Defense Assists': stats_defense.get('a', ''),
                                'Defense KAST': stats_defense.get('kast', ''),
                                'Defense ADR': stats_defense.get('adr', ''),
                            }
                            detailed_player_data.append(player_record)

            if detailed_player_data:
                detailed_player_df = pd.DataFrame(detailed_player_data)
                csv_files[f"vlr_detailed_player_stats_{timestamp}.csv"] = detailed_player_df.to_csv(index=False)

        # Create ZIP file and provide ONE-CLICK download
        if csv_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, csv_content in csv_files.items():
                    zip_file.writestr(filename, csv_content)

            zip_buffer.seek(0)

            # ONE CLICK DOWNLOAD - No button click needed
            st.download_button(
                label="📦 Download all CSV files (Zip)",
                data=zip_buffer.getvalue(),
                file_name=f"vlr_complete_data_{timestamp}.zip",
                mime="application/zip",
                help=f"Download all {len(csv_files)} CSV files in a single ZIP archive",
                use_container_width=True,
                type="secondary"
            )
        else:
            st.info("No data available to download")

    st.divider()

    # Additional CSV download options
    with st.expander("📁 Additional CSV Download Options", expanded=True):
        st.markdown("**Download specific data categories as CSV files:**")

        # Organize downloads in a clean 2x2 grid
        col1, col2 = st.columns(2)

        with col1:
            # Basic scraped data downloads
            st.markdown("**Basic Tournament Data:**")

            # Matches CSV
            if data.get('matches_data', {}).get('matches'):
                matches_df = pd.DataFrame(data['matches_data']['matches'])
                matches_csv = matches_df.to_csv(index=False)
                st.download_button(
                    label="🏆 Matches CSV",
                    data=matches_csv,
                    file_name=f"vlr_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Basic match results and information",
                    use_container_width=True
                )
            else:
                st.info("No matches data available")

            # Player stats CSV
            if data.get('stats_data', {}).get('player_stats'):
                stats_df = pd.DataFrame(data['stats_data']['player_stats'])
                stats_csv = stats_df.to_csv(index=False)
                st.download_button(
                    label="👥 Player Stats CSV",
                    data=stats_csv,
                    file_name=f"vlr_player_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Tournament player statistics",
                    use_container_width=True
                )
            else:
                st.info("No player stats data available")

        with col2:
            # Maps and agents data downloads
            st.markdown("**Maps & Agents Data:**")

            maps_agents_data = data.get('maps_agents_data', {})

            # Agent utilization CSV
            agents = maps_agents_data.get('agents', maps_agents_data.get('agent_stats', []))
            if agents:
                # Create simple agent data table - NO AGGREGATION
                agent_data = []
                for agent in agents:
                    agent_record = {
                        'Agent': agent.get('agent_name', agent.get('agent', 'Unknown')),
                        'Total_Utilization': agent.get('total_utilization', 0),
                        'Total_Utilization_Percent': agent.get('total_utilization_percent', '0%')
                    }

                    # Add map utilizations as separate columns
                    map_utils = agent.get('map_utilizations', [])
                    for map_util in map_utils:
                        if isinstance(map_util, dict):
                            map_name = map_util.get('map', '')
                            utilization = map_util.get('utilization_percent', 0)
                            agent_record[f"{map_name}_Utilization"] = utilization

                    agent_data.append(agent_record)

                if agent_data:
                    agents_df = pd.DataFrame(agent_data)
                    agents_csv = agents_df.to_csv(index=False)
                    st.download_button(
                        label="🎭 Agent Utilization CSV",
                        data=agents_csv,
                        file_name=f"vlr_agent_utilization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Agent utilization data as scraped",
                        use_container_width=True
                    )
                else:
                    st.info("No agent utilization data available")
            else:
                st.info("No agent data available")

            # Maps CSV
            maps = maps_agents_data.get('maps', maps_agents_data.get('map_stats', []))
            if maps:
                maps_df = pd.DataFrame(maps)
                maps_csv = maps_df.to_csv(index=False)
                st.download_button(
                    label="🗺️ Maps CSV",
                    data=maps_csv,
                    file_name=f"vlr_maps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Maps data as scraped",
                    use_container_width=True
                )
            else:
                st.info("No maps data available")

        # Detailed matches section (only if available)
        if data.get('detailed_matches'):
            st.divider()
            st.markdown("**Detailed Match Data:**")

            detailed_matches = data.get('detailed_matches', [])
            col_a, col_b = st.columns(2)

            with col_a:
                # Detailed matches CSV (consolidated format)
                detailed_csv_data = []
                for match in detailed_matches:
                    event_info = match.get('event_info', {})
                    teams = match.get('teams', {})
                    team1 = teams.get('team1', {})
                    team2 = teams.get('team2', {})

                    # Add match info
                    match_record = {
                        'Match ID': match.get('match_id', ''),
                        'Event': event_info.get('name', ''),
                        'Stage': event_info.get('stage', ''),
                        'Date UTC': event_info.get('date_utc', ''),
                        'Patch': event_info.get('patch', ''),
                        'Team 1': team1.get('name', ''),
                        'Team 2': team2.get('name', ''),
                        'Team 1 Score': team1.get('score_overall', ''),
                        'Team 2 Score': team2.get('score_overall', ''),
                        'Format': match.get('match_format', ''),
                        'Pick/Ban Info': match.get('map_picks_bans_note', ''),
                        'Match URL': match.get('match_url', ''),
                        'Scraped At': match.get('scraped_at', '')
                    }

                    # Add map details to the same record
                    maps_info = []
                    for map_data in match.get('maps', []):
                        map_info = f"{map_data.get('map_name', '')} ({map_data.get('team1_score_map', '')}-{map_data.get('team2_score_map', '')})"
                        maps_info.append(map_info)

                    match_record['Maps Played'] = ' | '.join(maps_info)
                    detailed_csv_data.append(match_record)

                if detailed_csv_data:
                    detailed_df = pd.DataFrame(detailed_csv_data)
                    detailed_csv = detailed_df.to_csv(index=False)
                    st.download_button(
                        label="🔍 Detailed Matches CSV",
                        data=detailed_csv,
                        file_name=f"vlr_detailed_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Detailed match information with map results",
                        use_container_width=True
                    )

            with col_b:
                # Detailed player stats CSV (using preferred format)
                detailed_player_data = []
                for match in detailed_matches:
                    match_id = match.get('match_id', '')
                    event_name = match.get('event_info', {}).get('name', '')

                    # Overall player stats (match-level)
                    for team_name, players in match.get('overall_player_stats', {}).items():
                        for player in players:
                            stats_all = player.get('stats_all_sides', {})
                            stats_attack = player.get('stats_attack', {})
                            stats_defense = player.get('stats_defense', {})

                            # Get all agents for this player across all maps
                            all_agents = player.get('agents', [])
                            primary_agent = player.get('agent', '')
                            all_agents_str = ', '.join(all_agents) if all_agents else primary_agent

                            player_record = {
                                'Match ID': match_id,
                                'Event': event_name,
                                'Map': 'Overall',
                                'Team': team_name,
                                'Player': player.get('player_name', ''),
                                'Player ID': player.get('player_id', ''),
                                'Primary Agent': primary_agent,
                                'All Agents': all_agents_str,

                                # All sides stats
                                'Rating': stats_all.get('rating', ''),
                                'ACS': stats_all.get('acs', ''),
                                'Kills': stats_all.get('k', ''),
                                'Deaths': stats_all.get('d', ''),
                                'Assists': stats_all.get('a', ''),
                                'K/D Diff': stats_all.get('kd_diff', ''),
                                'KAST': stats_all.get('kast', ''),
                                'ADR': stats_all.get('adr', ''),
                                'HS%': stats_all.get('hs_percent', ''),
                                'First Kills': stats_all.get('fk', ''),
                                'First Deaths': stats_all.get('fd', ''),
                                'FK/FD Diff': stats_all.get('fk_fd_diff', ''),

                                # Attack stats
                                'Attack Rating': stats_attack.get('rating', ''),
                                'Attack ACS': stats_attack.get('acs', ''),
                                'Attack Kills': stats_attack.get('k', ''),
                                'Attack Deaths': stats_attack.get('d', ''),
                                'Attack Assists': stats_attack.get('a', ''),
                                'Attack KAST': stats_attack.get('kast', ''),
                                'Attack ADR': stats_attack.get('adr', ''),

                                # Defense stats
                                'Defense Rating': stats_defense.get('rating', ''),
                                'Defense ACS': stats_defense.get('acs', ''),
                                'Defense Kills': stats_defense.get('k', ''),
                                'Defense Deaths': stats_defense.get('d', ''),
                                'Defense Assists': stats_defense.get('a', ''),
                                'Defense KAST': stats_defense.get('kast', ''),
                                'Defense ADR': stats_defense.get('adr', ''),
                            }
                            detailed_player_data.append(player_record)

                    # Map-by-map player stats
                    for map_data in match.get('maps', []):
                        map_name = map_data.get('map_name', '')
                        for team_name, players in map_data.get('player_stats', {}).items():
                            for player in players:
                                stats_all = player.get('stats_all_sides', {})
                                stats_attack = player.get('stats_attack', {})
                                stats_defense = player.get('stats_defense', {})

                                agent = player.get('agent', '')

                                player_record = {
                                    'Match ID': match_id,
                                    'Event': event_name,
                                    'Map': map_name,
                                    'Team': team_name,
                                    'Player': player.get('player_name', ''),
                                    'Player ID': player.get('player_id', ''),
                                    'Primary Agent': agent,
                                    'All Agents': agent,  # Single agent for individual map

                                    # All sides stats
                                    'Rating': stats_all.get('rating', ''),
                                    'ACS': stats_all.get('acs', ''),
                                    'Kills': stats_all.get('k', ''),
                                    'Deaths': stats_all.get('d', ''),
                                    'Assists': stats_all.get('a', ''),
                                    'K/D Diff': stats_all.get('kd_diff', ''),
                                    'KAST': stats_all.get('kast', ''),
                                    'ADR': stats_all.get('adr', ''),
                                    'HS%': stats_all.get('hs_percent', ''),
                                    'First Kills': stats_all.get('fk', ''),
                                    'First Deaths': stats_all.get('fd', ''),
                                    'FK/FD Diff': stats_all.get('fk_fd_diff', ''),

                                    # Attack stats
                                    'Attack Rating': stats_attack.get('rating', ''),
                                    'Attack ACS': stats_attack.get('acs', ''),
                                    'Attack Kills': stats_attack.get('k', ''),
                                    'Attack Deaths': stats_attack.get('d', ''),
                                    'Attack Assists': stats_attack.get('a', ''),
                                    'Attack KAST': stats_attack.get('kast', ''),
                                    'Attack ADR': stats_attack.get('adr', ''),

                                    # Defense stats
                                    'Defense Rating': stats_defense.get('rating', ''),
                                    'Defense ACS': stats_defense.get('acs', ''),
                                    'Defense Kills': stats_defense.get('k', ''),
                                    'Defense Deaths': stats_defense.get('d', ''),
                                    'Defense Assists': stats_defense.get('a', ''),
                                    'Defense KAST': stats_defense.get('kast', ''),
                                    'Defense ADR': stats_defense.get('adr', ''),
                                }
                                detailed_player_data.append(player_record)

                if detailed_player_data:
                    detailed_player_df = pd.DataFrame(detailed_player_data)
                    detailed_player_csv = detailed_player_df.to_csv(index=False)
                    st.download_button(
                        label="👥 Detailed Player Stats CSV",
                        data=detailed_player_csv,
                        file_name=f"vlr_detailed_player_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Detailed player statistics (overall + map-by-map)",
                        use_container_width=True
                    )


def display_example_urls():
    """Display example URLs"""
    st.header("📝 Example URLs")
    st.markdown("""
    Here are some example VLR.gg event URLs you can use:
    """)

    examples = [
        ("Valorant Champions 2024", "https://www.vlr.gg/event/2097/valorant-champions-2024"),
        ("Masters Madrid 2024", "https://www.vlr.gg/event/1921/champions-tour-2024-masters-madrid"),
        ("Masters Shanghai 2024", "https://www.vlr.gg/event/1999/champions-tour-2024-masters-shanghai"),
    ]

    for title, url in examples:
        st.code(f"{title}: {url}")

def main():
    """Main Streamlit application"""
    # Initialize session state
    init_session_state()

    # Sidebar for navigation
    with st.sidebar:
        st.title("🎮 VLR Scraper")

        page = st.radio(
            "Navigate to:",
            ["🔍 Scrape Data", "🗄️ Database", "📊 View Database Event"],
            key="navigation"
        )

        # Database quick stats in sidebar
        st.divider()
        st.subheader("📊 Database Stats")
        try:
            db_stats = st.session_state.db.get_database_stats()
            st.metric("Events", db_stats.get('total_events', 0))
            st.metric("Matches", db_stats.get('total_matches', 0))
            st.metric("Players", db_stats.get('unique_players', 0))
        except:
            st.error("Database connection issue")

    # Main content based on navigation
    if page == "🔍 Scrape Data":
        # Display header
        display_header()

        # URL input section
        url = display_url_input()
        st.divider()

        # Control panel
        scrape_clicked, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed_matches = display_control_panel(url)
        st.divider()

        # Progress section
        status_container = display_progress()
        st.divider()

        # Handle scraping
        if scrape_clicked and url:
            perform_scraping(url, scrape_matches, scrape_stats, scrape_maps_agents, scrape_detailed_matches, max_detailed_matches, status_container)

        # Display simple data preview if available
        if st.session_state.scraped_data:
            display_simple_data_preview()
            st.divider()

            # Save options
            display_save_options()
            st.divider()

            # Reset button
            if st.button("🔄 Start New Scraping Session", type="secondary"):
                st.session_state.scraped_data = None
                st.session_state.scraping_progress = 0
                st.session_state.scraping_status = "Ready to scrape..."
                st.session_state.current_step = "idle"
                st.rerun()
        else:
            # Show examples when no data
            display_example_urls()

    elif page == "🗄️ Database":
        # Database management page
        display_database_section()

    elif page == "📊 View Database Event":
        # Database event viewer
        display_database_event_data()

        # If no event is being viewed, show database section
        if not st.session_state.get('show_db_event', False):
            st.info("👆 Go to the Database page to select an event to view, or use the navigation above.")
            display_database_section()

if __name__ == "__main__":
    main()
