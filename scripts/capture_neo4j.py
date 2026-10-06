"""Capture the actual local Neo4j Browser viewport (optional: pip install playwright).

Run after the full benchmark, not after --check, which leaves a smaller graph.
Screenshots contain the entire web viewport, including editor and results; they
do not include the operating-system title bar or browser address bar.
"""
from pathlib import Path
import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright


QUERIES = {
    "kg_count": "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;",
    "kg_cross_kb": "MATCH p=(:Person)-[:INVOLVED_IN]->(:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) RETURN p LIMIT 25;",
    "kg_my_case": "MATCH p=(:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->() RETURN p,q;",
}


def main():
    load_dotenv()
    folder = Path("report/img")
    folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        page.goto("http://localhost:7474", wait_until="networkidle")
        page.locator("input[name=username]").fill(os.getenv("NEO4J_USER", "neo4j"))
        page.locator("input[name=password]").fill(os.getenv("NEO4J_PASSWORD", "password123"))
        page.get_by_role("button", name="Connect", exact=True).click()
        page.get_by_text("Connected to neo4j://localhost:7687", exact=True).wait_for()
        if page.get_by_role("button", name="Dismiss", exact=True).count():
            page.get_by_role("button", name="Dismiss", exact=True).click()
        editor = page.get_by_role("textbox", name="Cypher Editor")
        for name, query in QUERIES.items():
            editor.fill(":clear")
            editor.press("Control+Enter")
            page.wait_for_timeout(300)
            editor.fill(query)
            editor.press("Control+Enter")
            page.get_by_text("Started streaming", exact=False).wait_for(state="visible", timeout=30000)
            # Graph force layout needs a few frames to settle before artifact capture.
            page.wait_for_timeout(3500)
            print(name, page.locator("body").inner_text(), flush=True)
            page.screenshot(path=str(folder / f"{name}.png"))
        browser.close()


if __name__ == "__main__":
    main()
