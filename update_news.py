import feedparser
import time
import calendar
import requests
import argostranslate.package
import argostranslate.translate
from datetime import datetime, timedelta, timezone

CUTOFF = datetime.now(timezone.utc) - timedelta(hours=48)


def setup_translator():
    try:
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        package = next(
            (p for p in available if p.from_code == "en" and p.to_code == "uk"),
            None
        )
        if package:
            argostranslate.package.install_from_path(package.download())
    except Exception:
        pass


setup_translator()


def is_recent(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return True
    entry_time = datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    return entry_time >= CUTOFF

FEEDS = {
    "ISW": "https://www.understandingwar.org/rss.xml",
    "WSJ": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
    "Bloomberg": "https://feeds.bloomberg.com/politics/news.rss",
    "The Economist": "https://news.google.com/rss/search?q=site:economist.com+Ukraine&hl=uk&gl=UA&ceid=UA:uk",
    "Financial Times": "https://news.google.com/rss/search?q=site:ft.com+Ukraine&hl=uk&gl=UA&ceid=UA:uk",
    "NYT": "https://news.google.com/rss/search?q=site:nytimes.com+Ukraine&hl=uk&gl=UA&ceid=UA:uk",
}

WAR_KEYWORDS = ["ukraine", "russia", "putin", "zelensky", "zelenskyy",
                "kyiv", "kremlin", "moscow", "war"]


def is_war_related(entry):
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw in text for kw in WAR_KEYWORDS)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch_feed(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        return feedparser.parse(resp.content)
    except Exception:
        return feedparser.parse(url)


def translate(text):
    try:
        return argostranslate.translate.translate(text, "en", "uk")
    except Exception:
        return text


WEATHER_LAT, WEATHER_LON = 50.294063, 24.250816

WEATHER_CODES = {
    0: "ясно", 1: "переважно ясно", 2: "мінлива хмарність", 3: "хмарно",
    45: "туман", 48: "паморозь",
    51: "легка мряка", 53: "мряка", 55: "сильна мряка",
    61: "невеликий дощ", 63: "дощ", 65: "сильний дощ",
    71: "невеликий сніг", 73: "сніг", 75: "сильний сніг",
    80: "короткочасний дощ", 81: "зливи", 82: "сильні зливи",
    95: "гроза", 96: "гроза з градом", 99: "сильна гроза з градом",
}


def fetch_weather():
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={WEATHER_LAT}"
            f"&longitude={WEATHER_LON}&current_weather=true"
        )
        data = requests.get(url, timeout=15).json()["current_weather"]
        temp = round(data["temperature"])
        wind = round(data["windspeed"])
        desc = WEATHER_CODES.get(data["weathercode"], "")
        return f"{temp}°C, {desc}, вітер {wind} км/год"
    except Exception:
        return None

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
<p class="updated">Оновлено: __TIMESTAMP__ UTC</p>
"""
html = html.replace("__TIMESTAMP__", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

for name, url in FEEDS.items():
    html += f"<h2>{name}</h2>\n<ul>\n"
    feed = fetch_feed(url)
    entries = [e for e in feed.entries if is_recent(e)]
    if name != "ISW":
        entries = [e for e in entries if is_war_related(e)]
    entries = entries[:6]
    if not entries:
        html += "  <li><em>немає даних цього разу</em></li>\n"
    for entry in entries:
        title = entry.get("title", "")
        link = entry.get("link", "#")
        title_uk = translate(title)
        html += f'  <li><a href="{link}" target="_blank">{title_uk}</a></li>\n'
    html += "</ul>\n"
    time.sleep(2)

weather = fetch_weather()
html += '<h2>Погода</h2>\n'
if weather:
    html += f'<p>{weather}</p>\n'
else:
    html += '<p><em>не вдалося завантажити</em></p>\n'

html += '<p class="updated" style="margin-top:40px;">@IQAI01</p>\n'
html += "</body>\n</html>\n"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
