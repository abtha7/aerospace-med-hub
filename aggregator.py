import json
import urllib.request
import urllib.parse
from datetime import datetime
import feedparser

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AerospaceMedHub/1.0'}
TIMEOUT = 10

def fetch_pubmed_queries():
    """Fetches targeted PubMed queries for Aerospace Med & Flight Surgery."""
    articles = []
    queries = [
        ('("aerospace medicine" OR "space physiology" OR "flight surgeon" OR "microgravity human")', "Research"),
        ('("aerospace medicine residency" OR "space medicine training" OR "spaceflight medical")', "Residency")
    ]
    
    for q_string, category in queries:
        try:
            encoded_q = urllib.parse.quote(q_string)
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_q}&retmode=json&sort=pub_date&retmax=10"
            
            req = urllib.request.Request(search_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                search_data = json.loads(response.read().decode())
            
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if id_list:
                summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(id_list)}&retmode=json"
                req_sum = urllib.request.Request(summary_url, headers=HEADERS)
                with urllib.request.urlopen(req_sum, timeout=TIMEOUT) as resp:
                    summary_data = json.loads(resp.read().decode()).get("result", {})
                    for pmid in id_list:
                        item = summary_data.get(pmid, {})
                        title = item.get("title", "Untitled Paper")
                        
                        articles.append({
                            "id": f"pubmed-{pmid}",
                            "title": title,
                            "source": "PubMed",
                            "category": category,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "date": item.get("pubdate", datetime.utcnow().strftime('%Y-%m-%d'))
                        })
        except Exception as e:
            print(f"Warning: PubMed query '{category}' skipped: {e}")
            
    return articles

def fetch_rss(url, source_name, default_category):
    """Fetches and parses RSS feeds with automatic category detection."""
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            content = response.read()
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:8]:
                title = entry.get("title", "Untitled Entry")
                title_lower = title.lower()
                
                # Dynamic categorization based on keywords
                category = default_category
                if any(term in title_lower for term in ["residency", "fellowship", "rotation", "clerkship", "utmb", "mayo", "wright state"]):
                    category = "Residency"
                elif any(term in title_lower for term in ["grant", "scholarship", "opportunity", "job", "application", "apply"]):
                    category = "Opportunities"
                elif any(term in title_lower for term in ["conference", "meeting", "symposium", "webinar", "asma 202", "asgsr 202"]):
                    category = "Events"

                items.append({
                    "id": entry.get("id", entry.get("link", title)),
                    "title": title,
                    "source": source_name,
                    "category": category,
                    "url": entry.get("link", "#"),
                    "date": entry.get("published", entry.get("updated", datetime.utcnow().strftime('%Y-%m-%d')))
                })
    except Exception as e:
        print(f"Warning: {source_name} feed skipped: {e}")
    return items

def main():
    # Master List of RSS Sources & Smart Google News Streams
    sources = [
        # Professional Societies & Associations
        ("https://asma.org/news/asma-news/", "AsMA News", "Industry News"),
        ("https://news.google.com/rss/search?q=Aerospace+Medical+Association&hl=en-US&gl=US&ceid=US:en", "AsMA Coverage", "Industry News"),
        ("https://news.google.com/rss/search?q=ASGSR+gravitational+space+research&hl=en-US&gl=US&ceid=US:en", "ASGSR Updates", "Industry News"),
        
        # Residency & Medical Opportunities
        ("https://news.google.com/rss/search?q=%22aerospace+medicine+residency%22+OR+%22space+medicine+fellowship%22&hl=en-US&gl=US&ceid=US:en", "Residency News", "Residency"),
        ("https://news.google.com/rss/search?q=UTMB+%22aerospace+medicine%22&hl=en-US&gl=US&ceid=US:en", "UTMB Aerospace Med", "Residency"),
        ("https://news.google.com/rss/search?q=Mayo+Clinic+%22aerospace+medicine%22&hl=en-US&gl=US&ceid=US:en", "Mayo Clinic Aerospace", "Residency"),
        
        # Space Agencies & Research Journals
        ("https://www.nasa.gov/feed/", "NASA Main News", "Industry News"),
        ("https://www.nature.com/npjmgrav.rss", "npj Microgravity", "Research"),
        ("https://spacenews.com/feed/", "SpaceNews", "Industry News"),
        
        # Community & Reddit Feeds
        ("https://www.reddit.com/r/aerospace_medicine/new/.rss", "Reddit r/aerospace_medicine", "Community"),
        ("https://www.reddit.com/r/spacemedicine/new/.rss", "Reddit r/spacemedicine", "Community")
    ]
    
    aggregated = []
    
    # 1. Fetch targeted PubMed research & residency articles
    aggregated.extend(fetch_pubmed_queries())
    
    # 2. Fetch all RSS and Google News stream feeds
    for url, source, category in sources:
        aggregated.extend(fetch_rss(url, source, category))

    # Save output to data.json
    output = {
        "last_updated": datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        "items": aggregated
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Successfully compiled {len(aggregated)} items into data.json")

if __name__ == "__main__":
    main()
