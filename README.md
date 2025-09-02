# 🎮 VLR.gg Comprehensive Data Scraper

A modular web scraping solution for extracting comprehensive Valorant esports data from [VLR.gg](https://www.vlr.gg/). This project provides both programmatic access and a user-friendly web interface for collecting tournament data, player statistics, agent usage patterns, and detailed match analytics.

## 🚀 Features

### **Core Scraping Capabilities**
- **🏆 Match Data**: Tournament brackets, match results, scores, schedules, and team performance metrics
- **📊 Player Statistics**: Individual player rankings, performance metrics, and statistical analysis
- **🎭 Maps & Agents**: Agent usage patterns, map pick rates, and composition strategies
- **🔍 Detailed Match Analysis**: Round-by-round breakdowns with comprehensive metrics
- **💰 Economy Tracking**: Financial performance analysis per round and match
- **⚡ Performance Metrics**: Detailed player performance data and analytics

### **Technical Features**
- **🔄 Modular Architecture**: 7 specialized scrapers for different data types
- **📈 Progress Tracking**: Real-time scraping progress with status updates
- **💾 Multiple Export Formats**: CSV, JSON, and ZIP file support
- **⚡ Performance Optimization**: Configurable scraping limits and batch processing

### **User Interface**
- **🌐 Streamlit Web App**: Modern, responsive web interface
- **🎨 Intuitive Controls**: Simple three-step process (Scrape → Review → Save)
- **📊 Data Preview**: Interactive tables for data review before export
- **⚙️ Customizable Options**: Selective data scraping with configurable limits

## 🏗️ Project Architecture

```
Project Root/
├── 📁 scrapper/                    # Core scraping modules
│   ├── vlr_scraper_coordinator.py    # Main orchestrator
│   ├── matches_scraper.py            # Match data extraction
│   ├── player_stats_scraper.py       # Player statistics
│   ├── maps_agents_scraper.py        # Agent and map data
│   ├── match_details_scrapper.py     # Detailed match data for each individual match
│   ├── detailed_match_economy_scrapper.py      # Economy data
│   └── detailed_match_performance_scrapper_v2.py # Performance metrics
├── vlr_streamlit_ui.py         # Web application interface
├── 📁 html_structure/             # HTML snapshot script and samples
├── 📁 sample_data/                # Example output files
├── 📋 requirements.txt             # Python dependencies
└── 📖 README.md                   # This documentation
```

## 🛠️ Installation & Setup

### **Prerequisites**
- Python 3.7 or higher
- Chrome browser (for Selenium-based scrapers)
- ChromeDriver (automatically managed by webdriver-manager)

### **Quick Start**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Piyush86kumar/Valorant_vlr.gg_scrapper.git
   cd Valorant_vlr.gg_scrapper.git
   ```
3. **Create a virtual environment**
    ```bash
    conda create -p /desired/path/to/env python=3.12
    conda activate /desired/path/to/env
    ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the web interface**
   ```bash
   streamlit run vlr_streamlit_ui.py
   ```

4. **Open your browser** and navigate to the displayed URL 

## 📖 Usage Guide

### **Web Interface (Recommended)**

1. **🔍 Enter Event URL**
   - Paste a VLR.gg event URL (e.g., `https://www.vlr.gg/event/2097/valorant-champions-2024`)
   - Click "Validate" to verify the URL

2. **⚙️ Configure Scraping Options**
   - Select which data types to scrape
   - Set limits for detailed match analysis (3, 5, 10, 15, 20, or All)
   - Choose scraping depth based on your needs

3. **🚀 Start Scraping**
   - Click "Start Scraping" to begin data extraction
   - Monitor progress with real-time status updates
   - Wait for completion notification

4. **👁️ Review Data**
   - Preview scraped data in interactive tables
   - Verify data quality and completeness
   - Check scraping summary statistics

5. **💾 Export Data**
   - Download a ZIP archive with all data with CSV files
   - Export as a single JSON file

## 📄 License

This project is for educational and research purposes only. Please be respectful of VLR.gg's terms of service and use this tool responsibly.

## 🔗 Related Resources

- [VLR.gg Official Site](https://www.vlr.gg/)
- [Valorant Esports](https://playvalorant.com/en-us/esports/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Beautiful Soup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)

---

**Built with ❤️ for the Valorant esports community**