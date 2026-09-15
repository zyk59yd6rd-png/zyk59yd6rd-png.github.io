import feedparser
from deep_translator import GoogleTranslator
from datetime import datetime

FEEDS = {
    "ISW": "https://www.understandingwar.org/rss.xml",
    "WSJ (World)": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
    "Bloomberg Politics": "https://feeds.bloomberg.com/politics/news.rss",
    "The Economist": "https://news.google.com/rss/search?q=site:economist.com&hl=uk&gl=UA&ceid=UA:uk",
    "Financial Times": "https://news.google.com/rss/search?q=site:ft.com&hl=uk&gl=UA&ceid=UA:uk",
    "NYT": "https://news.google.com/rss/search?q=site:nytimes.com&hl=uk&gl=UA&ceid=UA:uk",
}

translator = GoogleTranslator(source="auto", target="uk")

html = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Новини</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 700px; margin: 24px auto; padding: 0 16px;
         background:#111; color:#eee; }
  h2 { border-bottom: 1px solid #444; padding-bottom: 8px; margin-top: 32px; }
  a { color: #6cf; text-decoration: none; }
  li { margin-bottom: 14px; line-height: 1.4; }
  .updated { color: #888; font-size: 0.85em; }
</style>
</head>
<body>
<p class="updated">Оновлено: {timestamp} UTC</p>
""".format(timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

for name, url in FEEDS.items():
    html += f"<h2>{name}</h2>\n<ul>\n"
    feed = feedparser.parse(url)
    for entry in feed.entries[:6]:
        title = entry.get("title", "")
        link = entry.get("link", "#")
        try:
            title_uk = translator.translate(title)
        except Exception:
            title_uk = title
        html += f'  <li><a href="{link}" target="_blank">{title_uk}</a></li>\n'
    html += "</ul>\n"

html += "</body>\n</html>\n"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
