import logging
import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from langdetect import detect, LangDetectException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_rss(url):
    logging.info(f"Fetching RSS from {url}")
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:10]:  # Limit to 10 most recent entries
            title = entry.title
            description = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
            link = entry.link
            results.append(f"Headline: {title}\nDescription: {description}\nLink: {link}\n")
        return "\n".join(results)
    except Exception as e:
        logging.error(f"Error fetching RSS from {url}: {str(e)}")
        return ""

def scrape_website(url, article=None, title=None, description=None, link=None):
    logging.info(f"Scraping website {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if article:
            articles = soup.select(article)[:10]  # Limit to 10 most recent articles
        else:
            articles = [soup]  # If no article selector, treat the whole page as one article
        
        results = []
        for article_elem in articles:
            title_text = article_elem.select_one(title).text.strip() if title else ""
            description_text = article_elem.select_one(description).text.strip()[:200] + '...' if description else ""
            link_elem = article_elem.select_one(link) if link else None
            link_url = link_elem['href'] if link_elem else url
            if not link_url.startswith('http'):
                link_url = url + link_url
            results.append(f"Headline: {title_text}\nDescription: {description_text}\nLink: {link_url}\n")
        return "\n".join(results)
    except Exception as e:
        logging.error(f"Error scraping website {url}: {str(e)}")
        return ""

def is_relevant(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

def categorize_content(text, category_keywords):
    for category, keywords in category_keywords.items():
        if is_relevant(text, keywords):
            return category
    return "Other"

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def main():
    logging.info("Starting Multilingual Employer Branding and Talent Attraction news aggregation")
    
    sources = [
        # English sources
        {"type": "rss", "url": "https://www.hrmagazine.co.uk/feed/"},
        {"type": "rss", "url": "https://www.personneltoday.com/feed/"},
        {"type": "rss", "url": "https://www.hrdive.com/feeds/news/"},
        {"type": "rss", "url": "https://www.shrm.org/rss/pages/rss.aspx"},
        {"type": "rss", "url": "https://www.marketingweek.com/feed/"},
        {"type": "rss", "url": "https://www.brandchannel.com/feed/"},
        {"type": "rss", "url": "https://blog.linkedin.com/feed"},
        {"type": "scrape", "url": "https://www.glassdoor.com/employers/blog/",
         "selectors": {"article": "article", "title": "h2", "description": "p", "link": "a.read-more"}},
        
        # Danish sources
        {"type": "rss", "url": "https://www.hrm.dk/feed/"},
        {"type": "rss", "url": "https://www.lederne.dk/rss"},
        {"type": "rss", "url": "https://www.jobindex.dk/cms/rss"},
        {"type": "scrape", "url": "https://www.djoef.dk/presse-og-nyheder.aspx",
         "selectors": {"article": "article", "title": "h2", "description": "p", "link": "a"}},
        {"type": "rss", "url": "https://www.business.dk/rss"},
        {"type": "rss", "url": "https://finans.dk/rss"},
    ]
    
    keywords = {
        "en": [
            "employer branding", "talent attraction", "recruitment challenges", "talent acquisition",
            "employee value proposition", "EVP", "company culture", "workplace culture",
            "talent retention", "employee engagement", "candidate experience", "talent shortage",
            "employer reputation", "workplace diversity", "inclusion", "remote work", "hybrid work",
            "skills gap", "talent management", "employee benefits", "work-life balance",
            "career development", "employer review", "talent pool", "talent pipeline"
        ],
        "da": [
            "employer branding", "tiltrækning af talent", "rekrutteringsudfordringer", "talent acquisition",
            "medarbejderværdiforslag", "EVP", "virksomhedskultur", "arbejdspladskultur",
            "fastholdelse af talent", "medarbejderengagement", "kandidatoplevelse", "talentmangel",
            "arbejdsgiver omdømme", "mangfoldighed på arbejdspladsen", "inklusion", "fjernarbejde", "hybrid arbejde",
            "kompetencekløft", "talentledelse", "medarbejdergoder", "work-life balance",
            "karriereudvikling", "arbejdsgiveranmeldelse", "talentpulje", "talentpipeline"
        ]
    }
    
    category_keywords = {
        "Research": {
            "en": ["study", "research", "survey", "analysis", "report", "findings"],
            "da": ["undersøgelse", "forskning", "analyse", "rapport", "resultater"]
        },
        "Campaigns": {
            "en": ["campaign", "initiative", "program", "strategy", "launch"],
            "da": ["kampagne", "initiativ", "program", "strategi", "lancering"]
        },
        "Case Studies": {
            "en": ["case study", "success story", "example", "best practice"],
            "da": ["case study", "succeshistorie", "eksempel", "best practice"]
        }
    }
    
    output = f"Multilingual Employer Branding and Talent Attraction Updates - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for source in sources:
        logging.info(f"Processing source: {source['url']}")
        output += f"From source: {source['url']}\n"
        if source['type'] == 'rss':
            content = fetch_rss(source['url'])
        else:
            content = scrape_website(source['url'], **source.get('selectors', {}))
        
        # Detect language, filter content for relevance and categorize
        for item in content.split('\n\n'):
            lang = detect_language(item)
            if lang in ['en', 'da'] and is_relevant(item, keywords[lang]):
                category = categorize_content(item, {cat: kw[lang] for cat, kw in category_keywords.items()})
                output += f"Language: {lang.upper()}\nCategory: {category}\n{item}\n---\n\n"
    
    with open('multilingual_employer_branding_updates.txt', 'w', encoding='utf-8') as f:
        f.write(output)
    logging.info("Multilingual employer branding updates have been written to multilingual_employer_branding_updates.txt")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise
