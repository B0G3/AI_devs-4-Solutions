import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger

log = get_logger("browser")

PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "pages")
os.makedirs(PAGES_DIR, exist_ok=True)


def _url_to_filename(url: str) -> str:
    name = re.sub(r"https?://", "", url)
    name = re.sub(r"[^\w\-]", "_", name).strip("_")
    return name[:100] + ".txt"


OKO_URL = os.getenv("OKO_URL", "")
OKO_LOGIN = os.getenv("OKO_LOGIN", "")
OKO_PASSWORD = os.getenv("OKO_PASSWORD", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})


def _simplify_html(html: str, base_url: str = "") -> str:
    """Extract visible text, links, and forms from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "meta", "noscript"]):
        tag.decompose()

    lines = []

    text = soup.get_text(separator="\n", strip=True)
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")
        label = a.get_text(strip=True)
        links.append(f"  [{label}]({href})")
    if links:
        lines.append("\n--- Links ---")
        lines.extend(links)

    for form in soup.find_all("form"):
        action = form.get("action", "")
        method = form.get("method", "get").upper()
        if not action.startswith("http"):
            action = base_url.rstrip("/") + "/" + action.lstrip("/")
        fields = []
        for inp in form.find_all(["input", "textarea", "select"]):
            name = inp.get("name", "")
            typ = inp.get("type", inp.name)
            fields.append(f"{name} ({typ})")
        lines.append(f"\n--- Form: {method} {action} ---")
        lines.append("Fields: " + ", ".join(fields))

    return "\n".join(lines)


@tool
def login() -> str:
    """Log in to the OKO security console using stored credentials.

    Returns the page content after login (simplified HTML).
    """
    log.info("login: fetching login page %s", OKO_URL)
    resp = session.get(OKO_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form")

    if form:
        action = form.get("action", "/")
        if not action.startswith("http"):
            action = OKO_URL.rstrip("/") + "/" + action.lstrip("/")
        method = form.get("method", "post").lower()

        data = {}
        for inp in form.find_all("input"):
            name = inp.get("name", "")
            val = inp.get("value", "")
            if name:
                data[name] = val

        if "login" in data:
            data["login"] = OKO_LOGIN
        if "password" in data:
            data["password"] = OKO_PASSWORD
        if "access_key" in data:
            data["access_key"] = AGENT_API_KEY

        log.info("login: submitting form %s %s fields=%s", method.upper(), action, list(data.keys()))
        if method == "post":
            resp = session.post(action, data=data)
        else:
            resp = session.get(action, params=data)
    else:
        log.info("login: no form found, posting credentials directly to %s", OKO_URL)
        resp = session.post(OKO_URL, data={
            "login": OKO_LOGIN,
            "password": OKO_PASSWORD,
            "key": AGENT_API_KEY,
        })

    log.info("login: response status=%d", resp.status_code)
    return _simplify_html(resp.text, OKO_URL)


@tool
def get_page(url: str) -> str:
    """Fetch and read a page from the OKO console (read-only).

    Returns simplified page content: visible text, links, and forms.
    Never use this tool to submit modifications — use call_api instead.

    Args:
        url: Full URL to fetch.
    """
    log.info("get_page: GET %s", url)
    resp = session.get(url)
    log.info("get_page: status=%d", resp.status_code)
    content = _simplify_html(resp.text, url)
    path = os.path.join(PAGES_DIR, _url_to_filename(url))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n{content}")
    log.info("get_page: saved to %s", path)
    return content
