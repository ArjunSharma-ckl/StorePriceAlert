import os
import sys
import json
from pathlib import Path
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def search_google_shopping(query: str, zip_code: str, radius: int = 5) -> dict:
    """Search Google Shopping using SERP API"""
    params = {
        "engine": "google_shopping",
        "q": query,
        "location": f"{zip_code}, United States",
        "hl": "en",
        "gl": "us",
        "api_key": os.getenv("SERP_API_KEY")
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        print(f"Error searching Google Shopping: {e}")
        return {}

def search_local_stores(query: str, location: str, radius: int = 5) -> dict:
    """Search for local stores using Google Local Results"""
    params = {
        "engine": "google",
        "q": f"{query} near {location}",
        "location": f"{location}, United States",
        "hl": "en",
        "gl": "us",
        "api_key": os.getenv("SERP_API_KEY")
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        print(f"Error searching local stores: {e}")
        return {}

if __name__ == "__main__":
    # Test search
    zip_code = os.getenv("DEFAULT_ZIP_CODE", "78704")
    
    print("Testing Google Shopping Search...")
    shopping_results = search_google_shopping("4K TV", zip_code)
    print(f"Found {len(shopping_results.get('shopping_results', []))} shopping results")
    
    print("\nTesting Local Store Search...")
    local_results = search_local_stores("Walmart", zip_code)
    print(f"Found {len(local_results.get('local_results', []))} local results")
    
    # Save results to file for inspection
    with open("shopping_results.json", "w") as f:
        json.dump({"shopping": shopping_results, "local": local_results}, f, indent=2)
    
    print("\nResults saved to shopping_results.json")
