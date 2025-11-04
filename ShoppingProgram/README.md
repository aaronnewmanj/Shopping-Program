# eBay Product Scraper with SQL Database Storage

This program fetches product listings from eBay using your secure server-side eBay API token, and stores them in a MySQL database. Users can configure their own database without needing access to the eBay API credentials.

Setup Instructions
1. Clone the repository
git clone https://github.com/aaronnewmanj/Shopping-Program.git
cd Shopping-Program
cd ShoppingProgram

2. Install Dependencies
pip install -r requirements.txt
# or
pip3 install -r requirements.txt

3. Configure Database

Create a .env file in the project folder (copy example below) and fill in your own database credentials:

DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=ListingDatabase
EBAY_TOKEN_PROXY_URL=https://shopping-program.onrender.com/get-ebay-token

Note: Users do not need eBay API keys as the program uses a secure token proxy I created seperately.

5. Run the program
python ShoppingProgram.py
# or
python3 ShoppingProgram.py

You will be prompted to enter the product name to search.
Then you can choose how many products to fetch.
Finally, choose how to sort the results:

Price ascending
Price descending
Seller rating ascending
Seller rating descending




