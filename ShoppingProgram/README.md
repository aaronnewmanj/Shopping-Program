# eBay Product Scraper with SQL Database Storage

This is a Python based eBay product scraper that fetches desired product details, organizes them by price or seller rating, and stores them in a MySQL database. The program leverages the official eBay API through a deployed token proxy server, ensuring that API credentials remain private. Built with a focus on secure API integration, database flexibility, and scalable design, it demonstrates practical use of Flask, REST APIs, and environment-based credential management. 

# Setup Instructions
**1. Clone the repository and enter correct directory**

git clone https://github.com/aaronnewmanj/Shopping-Program.git

cd Shopping-Program

cd ShoppingProgram


**2. Install Dependencies**

pip install -r requirements.txt

or

pip3 install -r requirements.txt


**3. Configure Database and eBay Token**

Create a .env file in the project folder (copy example below) and fill in your own database credentials:

DB_HOST=127.0.0.1

DB_USER=root

DB_PASSWORD=yourpassword

DB_NAME=ListingDatabase

EBAY_TOKEN_PROXY_URL=https://shopping-program.onrender.com/get-ebay-token


Note: Users do not need eBay API keys as the program uses a secure token proxy I created seperately.


**4. Run the program**

The final results may take some time to load, since it uses a free public server that sleeps after inactivity (max 50 seconds). Run:

python ShoppingProgram.py

or

python3 ShoppingProgram.py


You will be prompted to enter the product name to search.
Then you can choose how many products to fetch.
Finally, choose how to sort the results:

Price ascending

Price descending

Seller rating ascending

Seller rating descending






