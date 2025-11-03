# Amazon Product Scraper with SQL Storage

This program scrapes thoough amazon.com for desired product and stores them in a MySQL database, with user determined list size and order based on price or rating. 

1. Clone the repo:
   git clone https://github.com/aaronnewmanj/Shopping-Program.git
   cd Shopping-Program
   cd ShoppingProgram

2. Install Dependancies
    pip install -r requirements.txt

3. Configure Database
    Create a .env file in the same folder (copy from .env.examplefile ) and fill in your credentials:

    Example:
    DB_HOST=host (such as 127.0.0.1)
    DB_USER=root
    DB_PASSWORD=yourpassword
    DB_NAME=ListingDatabase

5. Run the program 
    python ShoppingProgram.py 
    or
    python3 ShoppingProgram.py 



