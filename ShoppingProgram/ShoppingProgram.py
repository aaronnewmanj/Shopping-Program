import os
from dotenv import load_dotenv
import mysql.connector as sqlconn
import requests

load_dotenv()  # Loads the user's database credentials

# ---------- CONFIG ----------
DB = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "passwd": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ListingDatabase"),
}

# Your token proxy server URL
TOKEN_PROXY_URL = os.getenv("EBAY_TOKEN_PROXY_URL", "https://ShoppingProgram.com/get-ebay-token")
EBAY_USE_SANDBOX = os.getenv("EBAY_USE_SANDBOX", "false").lower() in ("1", "true", "yes")

# Browse API endpoint
BROWSE_SEARCH_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search" if EBAY_USE_SANDBOX else "https://api.ebay.com/buy/browse/v1/item_summary/search"

# ---------- DB SETUP ----------
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
        SellerRating DECIMAL(3,2),
        Link TEXT
    );
""")

select_all = f"SELECT * FROM {table_name}"
delete_all = f"TRUNCATE TABLE {table_name}"
add_product = f"INSERT INTO {table_name} (product, price, SellerRating, link) VALUES (%s, %s, %s, %s)"

curs.execute(delete_all)
db.commit()

# ---------- USER INPUT ----------
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

# ---------- EBAY TOKEN ----------
def get_ebay_app_token():
    """
    Requests an access token from the token proxy server.
    """
    resp = requests.get(TOKEN_PROXY_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()["access_token"]

# ---------- SEARCH & PARSE ----------
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
        # Title
        title = item.get("title", "")[:255]

        # Price
        price_obj = item.get("price") or item.get("minPrice") or {}
        price_val = price_obj.get("value") or price_obj.get("price") or 0
        try:
            price = float(price_val)
        except Exception:
            price = 0.0

        # Seller Rating
        seller_rating = 0.0
        try:
            r = item.get("seller", {}).get("feedbackPercentage")
            if r is not None:
                seller_rating = float(r)
        except Exception:
            seller_rating = 0.0

        # Item URL
        link = item.get("itemWebUrl") or item.get("itemHref") or ""

        items.append((title, price, seller_rating, link))

    return items

# ---------- SORTING ----------
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
        return results

# ---------- DISPLAY ----------
def display_results(results):
    for i, item in enumerate(results, start=1):
        print("")
        print(f"#{i}")
        print(f"Title : {item[0]}")
        print(f"Price : {item[1]}")
        print(f"SellerRating: {item[2]}")
        print(f"Link  : {item[3]}")
        print("")

# ---------- MAIN FLOW ----------
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
