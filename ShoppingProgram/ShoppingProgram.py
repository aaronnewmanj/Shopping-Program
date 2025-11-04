import os
import time
import base64
from dotenv import load_dotenv
import mysql.connector as sqlconn
import requests

load_dotenv()

# CONFIGURATION
DB = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "passwd": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ListingDatabase"),
}

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_USE_SANDBOX = os.getenv("EBAY_USE_SANDBOX", "false").lower() in ("1", "true", "yes")

IDENTITY_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if EBAY_USE_SANDBOX else "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_SEARCH_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search" if EBAY_USE_SANDBOX else "https://api.ebay.com/buy/browse/v1/item_summary/search"

# DB SETUP 
db = sqlconn.connect(
    host=DB["host"],
    user=DB["user"],
    passwd=DB["passwd"],
    database=DB["database"],
)
curs = db.cursor()
table_name = "Listings"

curs.execute(f"DROP TABLE IF EXISTS {table_name}")
curs.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        Ranking INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        Product VARCHAR(255),
        Price DOUBLE,
        SellerRating DOUBLE,
        Link TEXT
    );
""")

select_all = f"SELECT * FROM {table_name}"
delete_all = f"TRUNCATE TABLE {table_name}"
add_product = f"INSERT INTO {table_name} (product, price, SellerRating, link) VALUES (%s, %s, %s, %s)"

curs.execute(delete_all)
db.commit()

# USER INPUT 
product_name = input("What are you shopping for? ").strip()
if not product_name:
    print("No product provided. Exiting.")
    exit(1)

try:
    product_max = int(input("How many products do you want in list? ").strip())
    if product_max <= 0:
        raise ValueError()
except Exception:
    print("Invalid number, defaulting to 10.")
    product_max = 10

# EBAY OAUTH 
_token_cache = {"token": None, "expires_at": 0}

def get_ebay_app_token():
    now = int(time.time())
    if _token_cache["token"] and now < _token_cache["expires_at"] - 30:
        return _token_cache["token"]

    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        raise RuntimeError("EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in the environment.")

    creds = base64.b64encode(f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    resp = requests.post(IDENTITY_URL, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
    j = resp.json()
    token = j.get("access_token")
    expires_in = int(j.get("expires_in", 0))
    if not token:
        raise RuntimeError(f"Failed to obtain eBay token: {j}")

    _token_cache["token"] = token
    _token_cache["expires_at"] = now + expires_in
    return token

# SEARCH & PARSE 
def search_ebay_items(query, limit=20):
    token = get_ebay_app_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    params = {
        "q": query,
        "limit": min(limit, 200)
    }

    resp = requests.get(BROWSE_SEARCH_URL, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    items = []
    summaries = data.get("itemSummaries", []) or []
    for item in summaries[:limit]:
        title = item.get("title", "")[:255]

        price_obj = item.get("price") or item.get("minPrice") or {}
        price_val = price_obj.get("value") or price_obj.get("price") or None
        try:
            price = float(price_val) if price_val is not None else 0.0
        except Exception:
            price = 0.0

        seller_rating = 0.0
        seller = item.get("seller")
        if seller and seller.get("feedbackPercentage") is not None:
            try:
                seller_rating = round(float(seller.get("feedbackPercentage")), 1)
            except Exception:
                seller_rating = 0.0

        link = item.get("itemWebUrl") or item.get("itemHref") or ""

        items.append((title, price, seller_rating, link))

    return items

# SORTING 
def sort_results(results):
    prompt = (
        "How do you want to sort the data?\n"
        "  1: price ascending\n"
        "  2: price descending\n"
        "  3: seller rating ascending\n"
        "  4: seller rating descending\n"
        "Choose 1/2/3/4: "
    )
    try:
        sort_choice = int(input(prompt).strip())
    except Exception:
        print("Invalid choice, defaulting to price ascending (1).")
        sort_choice = 1

    if sort_choice == 1:
        return sorted(results, key=lambda x: x[1])
    elif sort_choice == 2:
        return sorted(results, key=lambda x: x[1], reverse=True)
    elif sort_choice == 3:
        return sorted(results, key=lambda x: x[2])
    elif sort_choice == 4:
        return sorted(results, key=lambda x: x[2], reverse=True)
    else:
        print("Unknown choice, returning unsorted results.")
        return results

# DISPLAY 
def display_results(results):
    for i, item in enumerate(results, start=1):
        print("")
        print(f"#{i}")
        print(f"Title       : {item[0]}")
        print(f"Price       : ${item[1]}")
        print(f"SellerRating: {item[2]}%")
        print(f"Link        : {item[3]}")
        print("")


if __name__ == "__main__":
    try:
        raw_items = search_ebay_items(product_name, limit=product_max)
    except Exception as e:
        print("Failed to fetch items from eBay:", e)
        exit(1)

    items = sort_results(raw_items)
    display_results(items)

    # Save to DB
    for product in items:
        try:
            curs.execute(add_product, product)
        except Exception as e:
            print("DB insert failed for product:", product[0], "error:", e)
    db.commit()
    print(f"✅ Saved {len(items)} items to the database table `{table_name}`.")
