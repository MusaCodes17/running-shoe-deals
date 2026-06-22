"""
Standalone scraper test script
Run this to test the scraper without needing the full API

Usage:
    python test_scraper.py
"""
from app.scrapers.the_last_hunt import TheLastHuntScraper
import json


def test_scraper():
    """Test The Last Hunt scraper with various queries"""
    
    print("=" * 80)
    print("TESTING THE LAST HUNT SCRAPER")
    print("=" * 80)
    
    scraper = TheLastHuntScraper()
    
    # Test queries
    test_cases = [
        ("Nike", "Vaporfly"),
        ("Adidas", "Adizero"),
        ("Asics", "Metaspeed"),
        ("Puma", "Deviate")
    ]
    
    for brand, model in test_cases:
        print(f"\n{'=' * 80}")
        print(f"TESTING: {brand} {model}")
        print("=" * 80)
        
        try:
            # Search for products
            print(f"\n🔍 Searching for {brand} {model}...")
            products = scraper.search_products(brand, model)
            
            print(f"\n✅ Found {len(products)} products")
            
            if products:
                # Display summary of products found
                print("\n📦 Products Found:")
                for i, product in enumerate(products[:5], 1):  # Show first 5
                    print(f"\n{i}. {product.get('name', 'N/A')}")
                    print(f"   URL: {product.get('product_url', 'N/A')}")
                    print(f"   Price: ${product.get('price', 'N/A')}")
                    if product.get('original_price'):
                        print(f"   Original Price: ${product.get('original_price')}")
                    print(f"   In Stock: {product.get('in_stock', 'Unknown')}")
                
                # Get details for first product
                if len(products) > 0:
                    print(f"\n🔬 Getting detailed info for first product...")
                    first_product = products[0]
                    details = scraper.get_product_details(first_product['product_url'])
                    
                    if details:
                        print("\n✅ Product Details:")
                        print(json.dumps(details, indent=2))
                    else:
                        print("\n❌ Could not get product details")
            else:
                print("\n⚠️  No products found for this query")
                print("This might mean:")
                print("  - The retailer doesn't carry this brand/model")
                print("  - CSS selectors need adjustment")
                print("  - Search functionality changed on the website")
            
        except Exception as e:
            print(f"\n❌ Error testing {brand} {model}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNOTE: If no products were found, this could mean:")
    print("1. The retailer doesn't stock these shoes")
    print("2. Website structure has changed (selectors need updating)")
    print("3. Network/connectivity issues")
    print("\nNext steps:")
    print("- If products found: Great! Try running through the API")
    print("- If no products found: May need to adjust CSS selectors")
    print("- Check the website manually to confirm products exist")


def test_price_parsing():
    """Test price parsing functionality"""
    
    print("\n" + "=" * 80)
    print("TESTING PRICE PARSING")
    print("=" * 80)
    
    scraper = TheLastHuntScraper()
    
    test_prices = [
        "$199.99",
        "C$249.50",
        "Was $300 Now $199",
        "249.99",
        "$1,299.00",
        "  $  99.50  ",
        "Invalid price"
    ]
    
    for price_text in test_prices:
        parsed = scraper.parse_price(price_text)
        status = "✅" if parsed else "❌"
        print(f"{status} '{price_text}' → {parsed}")


if __name__ == "__main__":
    print("\n🏃‍♂️ Running Shoe Deal Finder - Scraper Test\n")
    
    # Test price parsing first
    test_price_parsing()
    
    # Then test actual scraping
    print("\n" + "=" * 80)
    input("Press Enter to start live scraping test (this will make real web requests)...")
    test_scraper()
    
    print("\n✅ All tests complete!")
    print("\nIf you saw products above, the scraper is working!")
    print("You can now use the API endpoints to scrape and save to database.")
