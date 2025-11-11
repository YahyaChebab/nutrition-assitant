import requests
import os
import json
from typing import List, Dict
from datetime import datetime

class PerplexityClient:
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai/chat/completions"
    
    def research_ingredients(self, location: str, budget: float) -> List[Dict]:
        """Research cheapest ingredients in location"""
        # If no API key, use mock data
        if not self.api_key:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Using mock ingredients (no API key)")
            return self._get_mock_ingredients(location, budget)
        
        prompt = f"""Find the cheapest nutritious foods currently available in {location} for a budget of ${budget} CAD. 
        Research local grocery stores, discount markets, and seasonal deals.
        Return as JSON array with this exact structure:
        [
            {{
                "name": "ingredient name",
                "price": price in CAD,
                "store": "store name",
                "category": "grains/proteins/vegetables/fruits/dairy/other",
                "unit": "per lb/per kg/per item"
            }}
        ]
        Focus on staples: grains, proteins, vegetables, fruits. Include at least 20-25 ingredients.
        Prioritize affordable options from discount stores and seasonal produce.
        Return ONLY valid JSON, no additional text."""
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that returns only valid JSON data about food prices and availability."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 3000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Extract JSON from response
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    if json_start != -1 and json_end > json_start:
                        try:
                            json_str = content[json_start:json_end]
                            ingredients = json.loads(json_str)
                            if isinstance(ingredients, list) and len(ingredients) > 0:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(ingredients)} ingredients from Perplexity API")
                                return ingredients
                        except json.JSONDecodeError as e:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] JSON decode error: {e}")
            
            # Fallback to mock data if API fails
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Using mock ingredients as fallback")
            return self._get_mock_ingredients(location, budget)
        
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Perplexity API error: {e}")
            return self._get_mock_ingredients(location, budget)
    
    def validate_recipe(self, recipe: Dict, available_ingredients: List[Dict]) -> bool:
        """Validate that recipe uses only available ingredients"""
        recipe_ingredients = recipe.get('ingredients', [])
        available_names = [ing['name'].lower() for ing in available_ingredients]
        
        for ingredient in recipe_ingredients:
            ingredient_name = ingredient.get('name', '').lower()
            # Check if ingredient is available (fuzzy match)
            if not any(avail in ingredient_name or ingredient_name in avail for avail in available_names):
                return False
        
        return True
    
    def _get_mock_ingredients(self, location: str, budget: float) -> List[Dict]:
        """Fallback mock ingredients for testing"""
        return [
            {"name": "Brown Rice", "price": 2.50, "store": "Walmart", "category": "grains", "unit": "per lb"},
            {"name": "Chicken Breast", "price": 4.99, "store": "Walmart", "category": "proteins", "unit": "per lb"},
            {"name": "Black Beans", "price": 1.25, "store": "Walmart", "category": "proteins", "unit": "per can"},
            {"name": "Eggs", "price": 2.99, "store": "Walmart", "category": "proteins", "unit": "per dozen"},
            {"name": "Potatoes", "price": 3.99, "store": "Walmart", "category": "vegetables", "unit": "per 5 lbs"},
            {"name": "Carrots", "price": 1.50, "store": "Walmart", "category": "vegetables", "unit": "per lb"},
            {"name": "Broccoli", "price": 2.99, "store": "Walmart", "category": "vegetables", "unit": "per lb"},
            {"name": "Onions", "price": 1.99, "store": "Walmart", "category": "vegetables", "unit": "per 3 lbs"},
            {"name": "Bananas", "price": 1.99, "store": "Walmart", "category": "fruits", "unit": "per lb"},
            {"name": "Apples", "price": 2.99, "store": "Walmart", "category": "fruits", "unit": "per lb"},
            {"name": "Whole Wheat Bread", "price": 2.50, "store": "Walmart", "category": "grains", "unit": "per loaf"},
            {"name": "Oats", "price": 2.99, "store": "Walmart", "category": "grains", "unit": "per container"},
            {"name": "Ground Turkey", "price": 4.50, "store": "Walmart", "category": "proteins", "unit": "per lb"},
            {"name": "Spinach", "price": 2.50, "store": "Walmart", "category": "vegetables", "unit": "per bag"},
            {"name": "Tomatoes", "price": 2.99, "store": "Walmart", "category": "vegetables", "unit": "per lb"},
            {"name": "Pasta", "price": 1.99, "store": "Walmart", "category": "grains", "unit": "per box"},
            {"name": "Canned Tuna", "price": 1.75, "store": "Walmart", "category": "proteins", "unit": "per can"},
            {"name": "Peanut Butter", "price": 3.50, "store": "Walmart", "category": "proteins", "unit": "per jar"},
            {"name": "Milk", "price": 4.99, "store": "Walmart", "category": "dairy", "unit": "per gallon"},
            {"name": "Cheese", "price": 3.99, "store": "Walmart", "category": "dairy", "unit": "per block"},
            {"name": "Yogurt", "price": 2.99, "store": "Walmart", "category": "dairy", "unit": "per container"},
            {"name": "Cabbage", "price": 1.99, "store": "Walmart", "category": "vegetables", "unit": "per head"},
            {"name": "Bell Peppers", "price": 2.50, "store": "Walmart", "category": "vegetables", "unit": "per lb"},
            {"name": "Garlic", "price": 1.50, "store": "Walmart", "category": "vegetables", "unit": "per bulb"},
            {"name": "Lentils", "price": 2.25, "store": "Walmart", "category": "proteins", "unit": "per lb"}
        ]
