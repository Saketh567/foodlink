import requests
from app import create_app
from app.utils.address_service import search_addresses

app = create_app()

def test_address_search():
    with app.app_context():
        print("Testing Canada Post Address Search...")
        query = "123 Main"
        results = search_addresses(query)
        
        if results:
            print(f"SUCCESS: Found {len(results)} suggestions for '{query}'")
            for i, res in enumerate(results[:3]):
                print(f"  {i+1}. {res['text']} ({res['description']})")
        else:
            print("FAILURE: No results found. Check API key or connection.")

if __name__ == "__main__":
    test_address_search()
