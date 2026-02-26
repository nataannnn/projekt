# scraper.py
import requests
from bs4 import BeautifulSoup

def scrape_real_willhaben(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Titel nicht gefunden"
        
        text_content = "".join([p.text + " " for p in soup.find_all(['p', 'div', 'span']) if len(p.text) > 50])
                
        # Bilder extrahieren (UNLIMITED, aber strictly willhaben cache)
        image_urls = []
        gallery = soup.find('div', {'data-testid': 'gallery-carousel'})
        
        if gallery:
            for img in gallery.find_all('img'):
                src = img.get('src') or img.get('data-flickity-lazyload')
                # Extrem strenger Filter: Nur echte Bilder, keine Thumbnails, keine Werbung
                if src and "cache.willhaben.at" in src and "_thumb" not in src:
                    if src not in image_urls:
                        image_urls.append(src)
                        
        return {
            "title": title,
            "text": text_content[:3000], 
            "image_urls": image_urls,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
