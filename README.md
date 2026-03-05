# VLR.gg  Data Scraper 

A modular, end-to-end scraping system for VLR.gg tournament events — extracting match results, player statistics, economy data, performance data, and detailed per-map player stats, with CSV and JSON export support.

## Demo
🚀 Live Demo: View the interactive vlr scraper on [Streamlit Cloud](https://valorant-vlr-gg-scrapper-app.streamlit.app/)

## Process Flow
<p align="center">
    <img src = "assets/process_flow.png" alt ="Process Flow" width="500" />
</p>

## 🚀 Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```
2. **Install system dependencies (required for Selenium/Chromium)**:
```
# Linux / Streamlit Cloud (packages.txt)
chromium
chromium-driver
```

3. **Run the application**:
```bash
streamlit run streamlit_app.py
```

4. **Use the scraper**:
   - Enter a VLR.gg event URL (e.g., `https://www.vlr.gg/event/2097/valorant-champions-2024`)
   - Select what to scrape (Matches, Player Stats, Maps & Agents)
   - Review the scraped data in interactive tables
   - Download as a CSV ZIP archive or a single JSON file

## 📁 Project Structure

```
c:\My Code\Val_Analysis\Project 5\
├───.gitignore
├───packages.txt
├───README (1).md
├───README.md
├───requirements.txt
├───streamlit_app.py
├───.devcontainer\
├───.git\
├───assets\
│   └───process_flow.png
├───html_structure\
│   ├───dragon-ranger-gaming-vs-bilibili-gaming-vct-2025-china-stage-2-gf.html
│   ├───generate_html_snapshot.py
│   ├───talon-vs-nongshim-redforce-vct-2025-pacific-stage-2-ur1.html
│   ├───vct-2025-americas-stage-2.html
│   ├───vct-2025-china-stage-2.html
│   ├───vlr_kru_vs_cloud9.html
│   └───vlr_performance_page.html
├───sample_data\
│   └───Valorant Masters Toronto 2025_csvs.zip
├───scrapper\
│   ├───__init__.py
│   ├───detailed_match_economy_scrapper.py
│   ├───detailed_match_performance_scrapper_v2.py
│   ├───maps_agents_scraper.py
│   ├───match_details_scrapper.py
│   ├───matches_scraper.py
│   ├───player_stats_scraper.py
│   ├───vlr_scraper_coordinator.py
│   └───__pycache__\
└───val_venv\
    ├───conda-meta\
    └───etc\
```

## 🎯 Features

### Modular Scraping (6 Modules)

| Module | Source Tab | Key Data |
|--------|-----------|----------|
| 🏆 **Matches Scraper** | `/event/matches/` | match_id, teams, scores, dates, stages, match URLs |
| 📊 **Player Stats Scraper** | `/event/stats/` | Rating, ACS, K/D, KAST, ADR, HS%, kills, clutches, FK |
| 🎭 **Maps & Agents Scraper** | `/event/agents/` | Agent pick rates per map, map win rates |
| 💰 **Economy Scraper** | `?game=all&tab=economy` | Pistol / Eco / Semi-eco / Semi-buy / Full-buy per team per map |
| ⚡ **Performance Scraper** | `?game=all&tab=performance` | 2K–5K multikills, 1v1–1v5 clutches, ECON, PL, DE |
| 🤖 **Detailed Match Scraper** | Full match pages (Selenium) | Per-player stats split by All / Attack / Defense sides |

### Data Export
- **📦 CSV ZIP Archive**: 10 individual CSV files covering all data types
- **{ } JSON Export**: Single enhanced JSON file with nested and pre-flattened structures

### User Interface
- **8-step pipeline**: Input → Validate → Event Info → Static Scraping → Per-Match Loop → Selenium → Merge → Preview → Download
- **Real-time progress**: Live scraping status updates
- **Interactive preview**: `st.dataframe()` tables, expandable per-match sections, per-map tabs

---

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
```
- Python 3.12.12
- streamlit
- requests
- beautifulsoup4
- pandas
- plotly
```

**System packages** (Streamlit Cloud — `packages.txt`):
```
chromium
chromium-driver
```

---

## ⚙️ Technical Notes

### Scraper Types

**requests + BeautifulSoup4** (5 of 6 scrapers — fast, ~<5s each):
- Matches, Player Stats, Maps & Agents, Economy, Performance scrapers
- URL pattern: `/event/{id}/{name}` → tab-specific sub-paths
- Economy/Performance append query params: `?game=all&tab=economy` / `?game=all&tab=performance`
- Random 1–3 second delay between per-match requests to avoid rate limiting

**Selenium + Chromium** (Detailed Match scraper — slow, necessary):
- Required because VLR.gg renders Attack/Defense tab stats via JavaScript
- Headless Chromium, `WebDriverWait` 10s for `.wf-table-inset.mod-overview`
- 2-second grace delay after page load for final JS rendering
- Driver is quit after every match to prevent memory leaks
- ChromeDriver path: `/usr/bin/chromedriver` on Linux/Cloud; `webdriver-manager` locally

### Deployment (Streamlit Cloud)
- `packages.txt` must list `chromium` and `chromium-driver`
- `packages.txt` must be saved as **clean UTF-8 — no BOM** (use GitHub web editor)
- ChromeDriver must use `/usr/bin/chromedriver` on cloud; use `platform.system()` check to switch locally
- Large tournaments at "All" match limit can take **10–30+ minutes** for detailed scraping

---

## 📝 Example URLs

- **Valorant Champions 2024**: `https://www.vlr.gg/event/2097/valorant-champions-2024`
- **Masters Madrid 2024**: `https://www.vlr.gg/event/1921/champions-tour-2024-masters-madrid`
- **Masters Shanghai 2024**: `https://www.vlr.gg/event/1999/champions-tour-2024-masters-shanghai`

## 📈 Future Enhancements

- Better cleaning,formating and validation of data
- Visualization Integration
---

**Note**: This tool is for educational and research purposes. Please respect VLR.gg's terms of service and use responsibly.