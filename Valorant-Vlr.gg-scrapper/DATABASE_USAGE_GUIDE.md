# VLR Database Usage Guide

## Overview

The VLR database has been updated to handle comprehensive detailed match data from the `match_details_scrapper.py`. It now supports advanced analytics with pandas, numpy, and other data analysis tools.

## Database Schema

### Core Tables

1. **events** - Tournament/event information
2. **matches** - Basic match results
3. **player_stats** - Aggregated player statistics
4. **agent_usage** - Agent utilization data

### New Detailed Match Tables

4. **detailed_matches** - Comprehensive match metadata
5. **map_details** - Individual map results and information
6. **detailed_player_stats** - Detailed player performance with attack/defense splits

## Key Features

### ✅ Comprehensive Data Storage
- Match metadata (teams, scores, format, picks/bans)
- Map-by-map results and durations
- Player stats with attack/defense splits
- Agent usage across all matches

### ✅ Advanced Analytics Support
- Player performance analysis
- Agent meta analysis
- Map competitiveness metrics
- Performance correlation analysis

### ✅ Export Capabilities
- CSV export for external analysis
- Pandas DataFrame integration
- Ready for visualization tools

## Usage Examples

### 1. Basic Database Operations

```python
from vlr_database import VLRDatabase

# Initialize database
db = VLRDatabase("vlr_data.db")

# Save comprehensive data (includes detailed matches)
event_id = db.save_comprehensive_data(scraped_data)

# Get event data
event_data = db.get_event_data(event_id)
```

### 2. Analytics Queries

```python
# Player performance analysis
player_stats = db.get_player_performance_analysis()
top_players = player_stats.nlargest(10, 'rating_all')

# Agent performance stats
agent_stats = db.get_agent_performance_stats()
best_agents = agent_stats.nlargest(5, 'avg_rating')

# Map analysis
map_stats = db.get_map_performance_stats()
competitive_maps = map_stats.nlargest(3, 'close_game_percentage')
```

### 3. Advanced Analytics with Pandas

```python
import pandas as pd
import numpy as np

# Get detailed player data
df = db.get_player_performance_analysis()

# Calculate custom metrics
df['kd_ratio'] = df['kills_all'] / df['deaths_all'].replace(0, 1)
df['impact_score'] = (df['rating_all'] * 0.4 + 
                     df['acs_all'] / 300 * 0.3 + 
                     df['kd_ratio'] * 0.3)

# Team performance comparison
team_stats = df.groupby('team_name').agg({
    'rating_all': 'mean',
    'acs_all': 'mean',
    'impact_score': 'mean'
}).round(2)

# Performance consistency analysis
consistency = df.groupby('player_name').agg({
    'rating_all': ['mean', 'std'],
    'acs_all': ['mean', 'std']
}).round(2)
```

## Data Export for External Analysis

### CSV Export
```python
# Export all analytics data
player_data = db.get_player_performance_analysis()
agent_data = db.get_agent_performance_stats()
map_data = db.get_map_performance_stats()

# Save to CSV
player_data.to_csv('player_analytics.csv', index=False)
agent_data.to_csv('agent_analytics.csv', index=False)
map_data.to_csv('map_analytics.csv', index=False)
```

### Use Cases for Exported Data
- **Excel/Google Sheets**: Create pivot tables and charts
- **Jupyter Notebooks**: Advanced statistical analysis
- **R/Python**: Machine learning and predictive modeling
- **Tableau/Power BI**: Professional dashboards
- **Academic Research**: Statistical analysis and visualization

## Database Statistics

The database tracks comprehensive statistics:

```python
stats = db.get_database_stats()
# Returns:
# - total_events
# - total_matches
# - total_detailed_matches
# - total_maps
# - total_player_records
# - total_detailed_player_records
# - total_agent_records
# - unique_players
# - unique_detailed_players
# - unique_teams
```

## Performance Optimizations

### Indexes
- All foreign keys are indexed
- Player names and agent names are indexed
- Match IDs are indexed for fast lookups

### Query Optimization
- Use parameterized queries for filtering
- Batch operations for bulk inserts
- Connection pooling for concurrent access

## Integration with Streamlit UI

The database seamlessly integrates with the Streamlit UI:

1. **Data Saving**: Detailed matches are automatically saved when scraped
2. **Visualization**: Rich analytics displays in the UI
3. **Export**: Direct export functionality from the UI
4. **Real-time**: Live database statistics and updates

## Testing and Validation

Run the test scripts to verify functionality:

```bash
# Test database functionality
python test_database_detailed.py

# Run analytics demo
python analytics_demo.py
```

## Next Steps

### Recommended Enhancements
1. **Machine Learning**: Predict match outcomes based on player stats
2. **Time Series Analysis**: Track player/team performance over time
3. **Advanced Visualizations**: Create interactive dashboards
4. **API Development**: Build REST API for external access
5. **Data Pipeline**: Automated data collection and processing

### Integration Opportunities
- **Discord Bots**: Real-time match statistics
- **Web Applications**: Public analytics dashboard
- **Mobile Apps**: Player performance tracking
- **Research**: Academic studies on esports performance

## Troubleshooting

### Common Issues
1. **Database Locked**: Close all connections before operations
2. **Missing Data**: Ensure detailed matches are scraped correctly
3. **Performance**: Use indexes and limit query results
4. **Memory**: Process large datasets in chunks

### Support
- Check test scripts for examples
- Review database schema for table structure
- Use analytics demo for usage patterns
- Refer to pandas documentation for data manipulation

---

**The VLR database is now ready for comprehensive esports analytics!** 🎮📊
