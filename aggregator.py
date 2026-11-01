import json
import urllib.request
import urllib.parse
from datetime import datetime
import feedparser

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AerospaceMedHub/1.0'}

def fetch_pubmed():
    query = urllib.parse.quote('("aerospace medicine" OR "space physiology" OR "space medicine")')
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmode=json&sort=pub_date&retmax=12"
    
    req = urllib.request.Request(search_url, headers=HEADERS)
    articles = []
    try:
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
        
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if id_list:
            summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(id_list)}&retmode=json"
            req_sum = urllib.request.Request(summary_url, headers=HEADERS)
            with urllib.request.urlopen(req_sum) as resp:
                summary_data = json.loads(resp.read().decode()).get("result", {})
                for pmid in id_list:
                    item = summary_data.get(pmid, {})
                    title = item.get("title", "Untitled Article")
                    
                    category = "Research"
                    if any(term in title.lower() for term in ["residency", "fellowship", "training", "clerkship"]):
                        category = "Residency"
                    
                    articles.append({
                        "id": pmid,
                        "title": title,
                        "source": "PubMed",
                        "category": category,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "date": item.get("pubdate", "")
                    })
    except Exception as e:
        print(f"Error fetching PubMed: {e}")
    return articles

def fetch_rss(url, source_name, default_category):
    items = []
    try:
        feed = feedparser.parse(url, agent=HEADERS['User-Agent'])
        for entry in feed.entries[:8]:
            title = entry.get("title", "No Title")
            title_lower = title.lower()
            
            # Intelligent category auto-tagging
            category = default_category
            if any(term in title_lower for term in ["residency", "fellowship", "rotation", "clerkship", "utmb", "mayo"]):
                category = "Residency"
            elif any(term in title_lower for term in ["grant", "scholarship", "opportunity", "opening", "job", "apply"]):
                category = "Opportunities"
            elif any(term in title_lower for term in ["conference", "meeting", "symposium", "webinar", "event"]):
                category = "Events"

            items.append({
                "id": entry.get("id", entry.get("link", "")),
                "title": title,
                "source": source_name,
                "category": category,
                "url": entry.get("link", "#"),
                "date": entry.get("published", entry.get("updated", datetime.utcnow().strftime('%Y-%m-%d')))
            })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    return items

def main():
    sources = [
        ("https://www.reddit.com/r/aerospace_medicine/.rss", "Reddit r/aerospace_medicine", "Community"),
        ("https://asma.org/news/asma-news/", "AsMA News", "Industry News"),
        ("https://www.nature.com/npjmgrav.rss", "npj Microgravity", "Research"),
        ("https://www.nasa.gov/feed/", "NASA News", "Industry News")
    ]
    
    aggregated = []
    aggregated.extend(fetch_pubmed())
    
    for url, source, category in sources:
        aggregated.extend(fetch_rss(url, source, category))

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            "items": aggregated
        }, f, indent=2)

if __name__ == "__main__":
    main()
