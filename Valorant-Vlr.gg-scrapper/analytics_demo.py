#!/usr/bin/env python3
"""
Demo script showing how to use the VLR database for analytics with pandas and numpy
"""

import pandas as pd
import numpy as np
from vlr_database import VLRDatabase
import warnings
warnings.filterwarnings('ignore')

def setup_database():
    """Initialize database connection"""
    return VLRDatabase("test_detailed_vlr.db")

def player_performance_analysis(db):
    """Analyze player performance across matches"""
    print("=== Player Performance Analysis ===")
    
    # Get all player performance data
    df = db.get_player_performance_analysis()
    
    if df.empty:
        print("No player data available")
        return
    
    print(f"Total player records: {len(df)}")
    
    # Top performers by rating
    print("\n🌟 Top 10 Players by Rating:")
    top_players = df.nlargest(10, 'rating_all')[['player_name', 'team_name', 'agent', 'rating_all', 'acs_all', 'kills_all']]
    print(top_players.to_string(index=False))
    
    # Player statistics summary
    print(f"\n📊 Player Performance Summary:")
    print(f"Average Rating: {df['rating_all'].mean():.2f}")
    print(f"Average ACS: {df['acs_all'].mean():.0f}")
    print(f"Average K/D: {(df['kills_all'] / df['deaths_all'].replace(0, 1)).mean():.2f}")
    
    # Team performance comparison
    print(f"\n🏅 Team Performance Comparison:")
    team_stats = df.groupby('team_name').agg({
        'rating_all': 'mean',
        'acs_all': 'mean',
        'kills_all': 'mean',
        'deaths_all': 'mean'
    }).round(2)
    team_stats['avg_kd'] = (team_stats['kills_all'] / team_stats['deaths_all']).round(2)
    print(team_stats.to_string())
    
    return df

def agent_meta_analysis(db):
    """Analyze agent meta and performance"""
    print("\n=== Agent Meta Analysis ===")
    
    # Get agent performance stats
    df = db.get_agent_performance_stats()
    
    if df.empty:
        print("No agent data available")
        return
    
    print(f"Total agents analyzed: {len(df)}")
    
    # Agent performance ranking
    print("\n🎭 Agent Performance Ranking:")
    agent_ranking = df[['agent', 'times_played', 'avg_rating', 'avg_acs', 'avg_kills']].round(2)
    print(agent_ranking.to_string(index=False))
    
    # Most popular agents
    print(f"\n📈 Most Popular Agents:")
    popular_agents = df.nlargest(5, 'times_played')[['agent', 'times_played', 'avg_rating']]
    print(popular_agents.to_string(index=False))
    
    # Best performing agents (min 5 games)
    print(f"\n⭐ Best Performing Agents (Rating):")
    best_agents = df.nlargest(5, 'avg_rating')[['agent', 'avg_rating', 'avg_acs', 'times_played']]
    print(best_agents.to_string(index=False))
    
    return df

def map_analysis(db):
    """Analyze map statistics and trends"""
    print("\n=== Map Analysis ===")
    
    # Get map performance stats
    df = db.get_map_performance_stats()
    
    if df.empty:
        print("No map data available")
        return
    
    print(f"Total maps analyzed: {len(df)}")
    
    # Map statistics
    print("\n🗺️ Map Statistics:")
    map_stats = df[['map_name', 'times_played', 'avg_total_rounds', 'avg_round_diff', 'close_game_percentage']].round(2)
    print(map_stats.to_string(index=False))
    
    # Most competitive maps (highest close game percentage)
    print(f"\n🔥 Most Competitive Maps:")
    competitive_maps = df.nlargest(3, 'close_game_percentage')[['map_name', 'close_game_percentage', 'times_played']]
    print(competitive_maps.to_string(index=False))
    
    return df

def advanced_analytics(db):
    """Perform advanced analytics using pandas and numpy"""
    print("\n=== Advanced Analytics ===")
    
    # Get detailed player stats
    player_df = db.get_player_performance_analysis()
    
    if player_df.empty:
        print("No data available for advanced analytics")
        return
    
    # Calculate advanced metrics
    player_df['kd_ratio'] = player_df['kills_all'] / player_df['deaths_all'].replace(0, 1)
    player_df['impact_score'] = (player_df['rating_all'] * 0.4 + 
                                 player_df['acs_all'] / 300 * 0.3 + 
                                 player_df['kd_ratio'] * 0.3)
    
    # Performance consistency analysis
    print("\n📈 Performance Consistency Analysis:")
    consistency_stats = player_df.groupby('player_name').agg({
        'rating_all': ['mean', 'std', 'count'],
        'acs_all': ['mean', 'std'],
        'impact_score': 'mean'
    }).round(2)
    
    # Flatten column names
    consistency_stats.columns = ['_'.join(col).strip() for col in consistency_stats.columns]
    consistency_stats = consistency_stats[consistency_stats['rating_all_count'] >= 2]  # Players with multiple games
    
    print("Top 5 Most Consistent Players (Low Rating Std Dev):")
    consistent_players = consistency_stats.nsmallest(5, 'rating_all_std')[['rating_all_mean', 'rating_all_std', 'impact_score_mean']]
    print(consistent_players.to_string())
    
    # Agent-specific performance
    print(f"\n🎯 Agent-Specific Performance Analysis:")
    agent_performance = player_df.groupby('agent').agg({
        'rating_all': 'mean',
        'acs_all': 'mean',
        'kd_ratio': 'mean',
        'first_kills_all': 'mean',
        'first_deaths_all': 'mean'
    }).round(2)
    
    agent_performance['fk_fd_ratio'] = (agent_performance['first_kills_all'] / 
                                       agent_performance['first_deaths_all'].replace(0, 1)).round(2)
    
    print("Agent Performance Summary:")
    print(agent_performance.to_string())
    
    # Correlation analysis
    print(f"\n🔗 Performance Correlation Analysis:")
    numeric_cols = ['rating_all', 'acs_all', 'kills_all', 'deaths_all', 'assists_all', 'adr_all', 'first_kills_all']
    correlation_matrix = player_df[numeric_cols].corr().round(2)
    
    print("Key Correlations with Rating:")
    rating_corr = correlation_matrix['rating_all'].sort_values(ascending=False)
    for metric, corr in rating_corr.items():
        if metric != 'rating_all':
            print(f"  {metric}: {corr}")
    
    return player_df

def export_analytics_data(db):
    """Export data for external analysis"""
    print("\n=== Exporting Analytics Data ===")
    
    try:
        # Get all data
        player_data = db.get_player_performance_analysis()
        agent_data = db.get_agent_performance_stats()
        map_data = db.get_map_performance_stats()
        
        # Export to CSV
        if not player_data.empty:
            player_data.to_csv('player_analytics.csv', index=False)
            print("✅ Player analytics exported to player_analytics.csv")
        
        if not agent_data.empty:
            agent_data.to_csv('agent_analytics.csv', index=False)
            print("✅ Agent analytics exported to agent_analytics.csv")
        
        if not map_data.empty:
            map_data.to_csv('map_analytics.csv', index=False)
            print("✅ Map analytics exported to map_analytics.csv")
        
        print("\n📊 Data exported successfully! You can now use these CSV files with:")
        print("  - Excel or Google Sheets for visualization")
        print("  - Jupyter notebooks for advanced analysis")
        print("  - R or other statistical software")
        print("  - Business intelligence tools like Tableau or Power BI")
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def main():
    """Run analytics demo"""
    print("🎮 VLR Database Analytics Demo")
    print("=" * 50)
    
    # Setup database
    db = setup_database()
    
    # Run analytics
    player_df = player_performance_analysis(db)
    agent_df = agent_meta_analysis(db)
    map_df = map_analysis(db)
    
    if player_df is not None and not player_df.empty:
        advanced_analytics(db)
        export_analytics_data(db)
    
    print("\n" + "=" * 50)
    print("✅ Analytics demo completed!")
    print("\nNext steps:")
    print("1. Use the exported CSV files for further analysis")
    print("2. Create visualizations with matplotlib/seaborn")
    print("3. Build dashboards with Streamlit or Plotly Dash")
    print("4. Integrate with machine learning models for predictions")

if __name__ == "__main__":
    main()
