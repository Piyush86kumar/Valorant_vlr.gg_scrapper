# VLR.gg  Data Scraper 

A modular scraping system for VLR.gg tournament events with SQLite database integration.

## 🚀 Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the application**:
```bash
streamlit run vlr_streamlit_ui.py
```

3. **Use the scraper**:
   - Enter a VLR.gg event URL (e.g., `https://www.vlr.gg/event/2097/valorant-champions-2024`)
   - Select what to scrape (Matches, Player Stats, Maps & Agents)
   - Review the complete scraped data
   - Save to database or download files

## 📁 Project Structure

```
├── matches_scraper.py          # Scrapes match data and results
├── player_stats_scraper.py     # Scrapes player statistics
├── maps_agents_scraper.py      # Scrapes agent usage and map data
├── vlr_scraper_coordinator.py  # Coordinates all scrapers
├── vlr_database.py             # SQLite database operations
├── vlr_streamlit_ui.py         # Streamlit web interface
└── README.md                   # This file
```

## 🎯 Features

### **Modular Scraping**
- **🏆 Matches Scraper**: Match details, scores, team performance
- **📊 Player Stats Scraper**: Individual player statistics and rankings
- **🎭 Maps & Agents Scraper**: Agent usage, map picks, meta analysis

### **Data Management**
- **🗄️ SQLite Database**: Persistent storage for historical analysis
- **📥 File Downloads**: JSON and CSV export options
- **👁️ Data Preview**: Complete data review before saving

### **User Interface**
- **Simple 3-step workflow**: Scrape → Review → Save
- **Real-time progress**: Live scraping status updates
- **Complete data display**: Full tables showing all scraped data

## 🔧 Usage Examples

### **Using Individual Scrapers**
```python
from matches_scraper import MatchesScraper

scraper = MatchesScraper()
matches_data = scraper.scrape_matches("https://www.vlr.gg/event/2097/valorant-champions-2024")
print(f"Found {matches_data['total_matches']} matches")
```

### **Using the Coordinator**
```python
from vlr_scraper_coordinator import VLRScraperCoordinator

coordinator = VLRScraperCoordinator()
data = coordinator.scrape_comprehensive(
    "https://www.vlr.gg/event/2097/valorant-champions-2024",
    scrape_matches=True,
    scrape_stats=True,
    scrape_maps_agents=True
)
```

### **Using the Database**
```python
from vlr_database import VLRDatabase

db = VLRDatabase()
event_id = db.save_comprehensive_data(scraped_data)
events = db.get_events_list()
```

## 📊 Data Structure

### **Matches Data**
- Team names and scores
- Match status (Completed/Scheduled)
- Stage and tournament information
- Series details

### **Player Statistics**
- Individual performance metrics (ACS, K/D, ADR, etc.)
- Team affiliations
- Rankings and comparisons

### **Maps & Agents Data**
- Agent usage percentages
- Win rates by agent
- Map pick rates
- Meta analysis with role categorization

## 🛠️ Requirements

- Python 3.7+
- streamlit
- requests
- beautifulsoup4
- pandas
- plotly

## 📝 Example URLs

- **Valorant Champions 2024**: `https://www.vlr.gg/event/2097/valorant-champions-2024`
- **Masters Madrid 2024**: `https://www.vlr.gg/event/1921/champions-tour-2024-masters-madrid`
- **Masters Shanghai 2024**: `https://www.vlr.gg/event/1999/champions-tour-2024-masters-shanghai`

## 🎮 Workflow

1. **Step 1 - Scrape**: Enter URL and select data types to scrape
2. **Step 2 - Review**: View complete scraped data in tables
3. **Step 3 - Save**: Choose database storage or file download

## 🔄 Database Features

- **Persistent Storage**: Save events for historical analysis
- **Easy Retrieval**: Browse and view previously scraped events
- **Export Options**: Export data to CSV files
- **Data Management**: View, delete, and organize saved events

## 📈 Future Enhancements

- Support for additional VLR.gg data types
- Advanced data visualization
- Automated scheduling for regular scraping
- API endpoint creation

---

**Note**: This tool is for educational and research purposes. Please respect VLR.gg's terms of service and use responsibly.