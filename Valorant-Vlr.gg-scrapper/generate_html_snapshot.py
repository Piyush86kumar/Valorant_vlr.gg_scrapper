#!/usr/bin/env python3
"""
This script uses Selenium to fetch the full, JavaScript-rendered HTML
of a given URL and saves it to a file. This is useful for debugging
web scrapers that need to deal with dynamic content.
"""

import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException

def generate_html_snapshot(url: str, output_file: str, wait_time: int = 5):
    """
    Fetches the full HTML of a URL using a headless browser and saves it.

    Args:
        url (str): The URL to fetch.
        output_file (str): The path to save the HTML file.
        wait_time (int): Time in seconds to wait for the page to load.
    """
    print(f"Initializing headless browser...")

    # Configure Selenium options
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        # Initialize WebDriver
        # Assumes chromedriver is in PATH or managed by a library like webdriver-manager
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        print(f"Navigating to: {url}")
        driver.get(url)

        print(f"Waiting {wait_time} seconds for dynamic content to load...")
        time.sleep(wait_time)

        # Get the full page source after JavaScript has executed
        full_html = driver.page_source

        print(f"Saving page structure to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(full_html)

        print(f"Successfully saved HTML snapshot to '{output_file}'.")
        print(f"   File size: {len(full_html) / 1024:.2f} KB")

    except WebDriverException as e:
        print(f"A WebDriver error occurred. Please ensure ChromeDriver is installed and in your system's PATH.")
        print(f"   Error details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and save the full HTML structure of a web page using Selenium.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("url", help="The full URL of the web page to capture.")
    parser.add_argument("-o", "--output", default="page_snapshot.html", help="Name of the output HTML file. (default: page_snapshot.html)")
    parser.add_argument("-w", "--wait", type=int, default=5, help="Seconds to wait for the page's JavaScript to render. (default: 5)")

    args = parser.parse_args()
    generate_html_snapshot(args.url, args.output, args.wait)