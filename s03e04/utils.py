import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path

HUB_URL = os.getenv("HUB_URL", "")
MEMORY_DIR = Path(__file__).parent / "memory"


def fetch_csv_files():
    base_url = f"{HUB_URL}/dane/s03e04_csv/"
    response = requests.get(base_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".csv")]

    MEMORY_DIR.mkdir(exist_ok=True)
    for filename in links:
        file_url = base_url + filename
        r = requests.get(file_url)
        r.raise_for_status()
        dest = MEMORY_DIR / filename
        dest.write_bytes(r.content)
        print(f"Downloaded: {filename}")

    print(f"Fetched {len(links)} CSV files to {MEMORY_DIR}")
