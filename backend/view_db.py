"""
Quick database viewer script
Run this to see what's in your database
"""
import sqlite3
from tabulate import tabulate

def view_database():
    # Connect to database
    conn = sqlite3.connect('shoe_deals.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("RUNNING SHOE DEAL FINDER - DATABASE CONTENTS")
    print("=" * 80)
    
    # View Shoes
    print("\n📦 SHOES")
    print("-" * 80)
    cursor.execute("""
        SELECT id, brand, model, target_price, is_active
        FROM shoes
        ORDER BY brand, model
    """)
    shoes = cursor.fetchall()
    if shoes:
        headers = ["ID", "Brand", "Model", "Target Price", "Active"]
        print(tabulate(shoes, headers=headers, tablefmt="grid"))
    else:
        print("No shoes in database")
    
    # View Retailers
    print("\n🏪 RETAILERS")
    print("-" * 80)
    cursor.execute("""
        SELECT id, name, base_url, is_active, scraping_enabled 
        FROM retailers 
        ORDER BY name
    """)
    retailers = cursor.fetchall()
    if retailers:
        headers = ["ID", "Name", "Base URL", "Active", "Scraping"]
        print(tabulate(retailers, headers=headers, tablefmt="grid"))
    else:
        print("No retailers in database")
    
    # View Price Records
    print("\n💰 PRICE RECORDS")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            pr.id,
            s.brand || ' ' || s.model as shoe,
            r.name as retailer,
            pr.price,
            pr.in_stock,
            pr.scraped_at
        FROM price_records pr
        JOIN shoes s ON pr.shoe_id = s.id
        JOIN retailers r ON pr.retailer_id = r.id
        ORDER BY pr.scraped_at DESC
        LIMIT 10
    """)
    prices = cursor.fetchall()
    if prices:
        headers = ["ID", "Shoe", "Retailer", "Price", "In Stock", "Scraped At"]
        print(tabulate(prices, headers=headers, tablefmt="grid"))
        
        total_count = cursor.execute("SELECT COUNT(*) FROM price_records").fetchone()[0]
        print(f"\nShowing 10 most recent. Total price records: {total_count}")
    else:
        print("No price records in database")
    
    # View Deals
    print("\n🎯 ACTIVE DEALS")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            d.id,
            s.brand || ' ' || s.model as shoe,
            r.name as retailer,
            d.current_price,
            d.target_price,
            d.savings_percent,
            d.is_active
        FROM deals d
        JOIN shoes s ON d.shoe_id = s.id
        JOIN retailers r ON d.retailer_id = r.id
        WHERE d.is_active = 1
        ORDER BY d.savings_percent DESC
    """)
    deals = cursor.fetchall()
    if deals:
        headers = ["ID", "Shoe", "Retailer", "Current $", "Target $", "Savings %", "Active"]
        print(tabulate(deals, headers=headers, tablefmt="grid"))
    else:
        print("No active deals in database")
    
    # Summary Stats
    print("\n📊 SUMMARY STATISTICS")
    print("-" * 80)
    stats = []
    
    total_shoes = cursor.execute("SELECT COUNT(*) FROM shoes").fetchone()[0]
    stats.append(["Total Shoes", total_shoes])
    
    active_shoes = cursor.execute("SELECT COUNT(*) FROM shoes WHERE is_active = 1").fetchone()[0]
    stats.append(["Active Shoes", active_shoes])
    
    total_retailers = cursor.execute("SELECT COUNT(*) FROM retailers").fetchone()[0]
    stats.append(["Total Retailers", total_retailers])
    
    active_retailers = cursor.execute("SELECT COUNT(*) FROM retailers WHERE is_active = 1").fetchone()[0]
    stats.append(["Active Retailers", active_retailers])
    
    total_prices = cursor.execute("SELECT COUNT(*) FROM price_records").fetchone()[0]
    stats.append(["Total Price Records", total_prices])
    
    total_deals = cursor.execute("SELECT COUNT(*) FROM deals WHERE is_active = 1").fetchone()[0]
    stats.append(["Active Deals", total_deals])
    
    print(tabulate(stats, headers=["Metric", "Count"], tablefmt="grid"))
    
    print("\n" + "=" * 80)
    
    conn.close()

if __name__ == "__main__":
    try:
        view_database()
    except sqlite3.OperationalError as e:
        print(f"Error: Could not open database. Make sure 'shoe_deals.db' exists.")
        print(f"Run 'python seed_data.py' first if you haven't already.")
        print(f"\nError details: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
