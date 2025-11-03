import os
from dotenv import load_dotenv
import mysql.connector as sqlconn
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin, parse_qs, unquote

load_dotenv()

db = sqlconn.connect(
    host = os.getenv("DB_HOST", "127.0.0.1"),
    user = os.getenv("DB_USER", "root"),
    passwd = os.getenv("DB_PASSWORD", ""),
    database = os.getenv("DB_NAME", "ListingDatabase"),
)

curs = db.cursor()
table_name = "Listings"

curs.execute(f"DROP TABLE IF EXISTS {table_name}")
curs.execute(f"""
             CREATE TABLE IF NOT EXISTS {table_name} (
             Ranking INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
             Product VARCHAR(255), 
             Price DOUBLE, 
             Rating DECIMAL(2, 1), 
             Link VARCHAR(255));
             """
)

select_all = f"SELECT * FROM {table_name}"
delete_all = f"TRUNCATE TABLE {table_name}"
add_product = f"INSERT INTO {table_name} (product, price, rating, link) VALUES (%s, %s, %s, %s)"

curs.execute(delete_all)

product_name = input("What are you shopping for? ")

url =f"https://www.amazon.com/s?k={product_name}"

product_max = int(input("How many products do you want in list? "))

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_html(url):
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text

def sort_results(results):
    sort_choice = int(input("How do you want to sort the data (1 or 2 for ascending or descending price, 3 or 4 for ascending or descending rating): "))

    if sort_choice==1:
        sorted_results = sorted(results, key=lambda x: x[1])
        return sorted_results

    elif sort_choice==2:
        sorted_results = sorted(results, key=lambda x: x[1], reverse = True)
        return sorted_results
        
    elif sort_choice==3:
        sorted_results = sorted(results, key=lambda x: x[2])
        return sorted_results
        
    elif sort_choice==4:
        sorted_results = sorted(results, key=lambda x: x[2], reverse = True)
        return sorted_results

def parse_product(url):
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")
    results = []

    for item in soup.select("div.s-main-slot div[data-component-type='s-search-result']")[:product_max]:
        title_el = item.find("h2")
        title = title_el.get_text(strip=True) if title_el else "N/A"

        link = "N/A"

        link_el = item.select_one("h2 a") or \
                  item.select_one("a.a-link-normal.s-no-outline") or \
                  item.select_one("a.a-link-normal")

        raw_href = link_el.get("href", "") if link_el else ""

        def unwrap_redirect(href):
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            for key in ("url", "u", "target", "redirect", "rd", "r", "link"):
                if key in qs and qs[key]:
                    candidate = qs[key][0]
                    return unquote(candidate)
            decoded = unquote(href)
            if "/dp/" in decoded or "/gp/" in decoded:
                return decoded
            return None

        if raw_href:
            if "sspa/click" in raw_href or "smile.amazon" in raw_href and ("redirect" in raw_href or "url=" in raw_href):
                candidate = unwrap_redirect(raw_href)
                if candidate:
                    parsed_cand = urlparse(candidate)
                    path = parsed_cand.path if parsed_cand.path else candidate
                else:
                    path = urlparse(raw_href).path
            else:
                path = urlparse(raw_href).path if urlparse(raw_href).path else raw_href

            m = re.search(r'(/dp/[^/]+)|(/gp/product/[^/]+)|(/gp/[^/]+)', path, flags=re.IGNORECASE)
            if m:
                clean_path = m.group(0)
                link = urljoin("https://www.amazon.com", clean_path)
            else:
                decoded_path = unquote(path)
                m2 = re.search(r'([A-Z0-9]{10})', decoded_path, flags=re.IGNORECASE)
                if m2:
                    asin = m2.group(1)
                    link = "https://www.amazon.com/dp/" + asin
                else:
                    link = urljoin("https://www.amazon.com", path.split('?')[0])
        else:
            asin = item.get("data-asin") or ""
            if asin:
                link = "https://www.amazon.com/dp/" + asin

        price_whole = item.select_one(".a-price .a-offscreen")
        price_text = price_whole.get_text(strip=True) if price_whole else "N/A"
        if price_text != "N/A":
            price = float(price_text[1:])
        else:
            price = 0

        rating_el = item.select_one("span.a-icon-alt")
        rating_text = rating_el.get_text(strip=True) if rating_el else "N/A"
        if rating_text != "N/A":
            rating = float(rating_text[:3])
        else:
            rating = 0

        results.append((title, price, rating, link))
    
    results = sort_results(results)
    return results

def display_results(result):
    for i in range (len(result)):
        print("")
        for j in range (4):
            print(result[i][j]) 
        print("")

products = parse_product(url)
display_results(products)

for product in products:
    curs.execute(add_product, product)

db.commit()
