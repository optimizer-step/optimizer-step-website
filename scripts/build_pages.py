"""Copy the browser-only site into the GitHub Pages /docs publishing folder."""
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
OUTPUT.mkdir(exist_ok=True)

for filename in (
    "index.html",
    "app.js",
    "playground.js",
    "launchCampaign.js",
    "styles.css",
    "favicon.svg",
    "favicon.ico",
):
    copyfile(ROOT / filename, OUTPUT / filename)

(OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
print(f"GitHub Pages files ready in {OUTPUT}")
