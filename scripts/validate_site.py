from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"src", "href"} and value and value.startswith("/") and not value.startswith("//"):
                self.refs.append(value.split("#", 1)[0].split("?", 1)[0])


files = [ROOT / "index.html", *(ROOT / "blog").glob("*.html")]
missing: list[tuple[str, str]] = []
for path in files:
    parser = RefParser()
    parser.feed(path.read_text(encoding="utf-8"))
    for ref in parser.refs:
        if not ref or ref.endswith("/"):
            continue
        if not (ROOT / ref.lstrip("/")).exists():
            missing.append((path.relative_to(ROOT).as_posix(), ref))

print(f"HTML files: {len(files)}")
print(f"Missing local assets: {missing}")
if missing:
    raise SystemExit(1)
