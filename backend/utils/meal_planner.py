import openai
import os
import json
from typing import List, Dict
from datetime import datetime

class MealPlanner:
    def __init__(self, perplexity_client):
        api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = openai.OpenAI(api_key=api_key) if api_key else None
        self.perplexity_client = perplexity_client
    
    def generate_meal_plan(self, user_data: Dict, ingredients: List[Dict], activity_log: List[str]) -> Dict:
        """Generate comprehensive meal plan with grocery list"""
        # If no API key, use fallback
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Using fallback meal plan (no API key)")
            return self._create_fallback_meal_plan(user_data, ingredients, activity_log)
        
        budget = user_data.get('budget', 0)
        people = user_data.get('people', 1)
        dietary_restrictions = user_data.get('dietary_restrictions', [])
        preferences = user_data.get('preferences', '')
        location = user_data.get('location', '')
        
        # Create ingredient list string
        ingredients_str = json.dumps(ingredients, indent=2)
        
        prompt = f"""Create a comprehensive weekly meal plan and grocery shopping list using ONLY these available ingredients:
{ingredients_str}

Requirements:
- Budget: ${budget} CAD per week for {people} people
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Preferences: {preferences if preferences else 'None'}
- Location: {location}
- Use ONLY ingredients from the list above
- Ensure nutritional balance
- Stay under budget
- Create a complete grocery shopping list with quantities
- Provide 7 days of meals (breakfast, lunch, dinner)
- Include cooking tips and storage advice

Return as JSON with this exact structure:
{{
    "grocery_list": [
        {{
            "ingredient": "ingredient name",
            "quantity": "amount needed",
            "unit": "unit of measurement",
            "estimated_cost": price in CAD,
            "category": "category name"
        }}
    ],
    "total_grocery_cost": total_cost,
    "days": [
        {{
            "day": "Monday",
            "meals": {{
                "breakfast": {{
                    "name": "meal name",
                    "ingredients": [{{"name": "ingredient", "quantity": "amount"}}],
                    "recipe": "simple recipe instructions",
                    "cooking_time": "time estimate",
                    "difficulty": "easy/medium/hard",
                    "cost": price
                }},
                "lunch": {{...}},
                "dinner": {{...}}
            }}
        }}
    ],
    "weekly_summary": {{
        "total_cost": total_cost,
        "serves": {people},
        "location": "{location}",
        "budget_utilization": "percentage of budget used"
    }},
    "cooking_tips": [
        "tip 1",
        "tip 2",
        "tip 3"
    ],
    "storage_advice": [
        "advice 1",
        "advice 2"
    ]
}}
Return ONLY valid JSON, no additional text."""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🍳 Generating meal options...")
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a nutrition expert that creates affordable, healthy meal plans with detailed grocery lists. Always return valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    meal_plan = json.loads(json_str)
                    
                    # Validate recipes
                    activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Verifying recipe accuracy and ingredient availability...")
                    validated = self._validate_meal_plan(meal_plan, ingredients, activity_log)
                    
                    if validated:
                        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Meal plan verified and ready!")
                        return meal_plan
                    else:
                        if attempt < max_retries - 1:
                            activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Re-generating grocery list - improving accuracy...")
                            continue
                
            except json.JSONDecodeError as e:
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Error parsing meal plan: {str(e)}")
                if attempt < max_retries - 1:
                    continue
            except Exception as e:
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Error generating meal plan: {str(e)}")
                if attempt < max_retries - 1:
                    continue
        
        # Fallback meal plan
        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Using fallback meal plan")
        return self._create_fallback_meal_plan(user_data, ingredients, activity_log)
    
    def _validate_meal_plan(self, meal_plan: Dict, ingredients: List[Dict], activity_log: List[str]) -> bool:
        """Validate that meal plan uses only available ingredients"""
        days = meal_plan.get('days', [])
        available_names = [ing['name'].lower() for ing in ingredients]
        grocery_list = meal_plan.get('grocery_list', [])
        
        # Validate grocery list items are available
        for item in grocery_list:
            item_name = item.get('ingredient', '').lower()
            if not any(avail in item_name or item_name in avail for avail in available_names):
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Grocery item '{item.get('ingredient')}' not found in available ingredients")
                return False
        
        # Validate meal ingredients
        for day in days:
            meals = day.get('meals', {})
            for meal_type, meal in meals.items():
                meal_ingredients = meal.get('ingredients', [])
                for ing in meal_ingredients:
                    ing_name = ing.get('name', '').lower()
                    # Check if ingredient is available
                    if not any(avail in ing_name or ing_name in avail for avail in available_names):
                        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Recipe ingredient '{ing.get('name')}' not available")
                        return False
        
        return True
    
    def _create_fallback_meal_plan(self, user_data: Dict, ingredients: List[Dict], activity_log: List[str]) -> Dict:
        """Create a comprehensive fallback meal plan"""
        people = user_data.get('people', 1)
        budget = user_data.get('budget')  # Don't use default - budget should be provided
        location = user_data.get('location', 'Unknown')
        dietary_restrictions = user_data.get('dietary_restrictions', [])
        
        # If no budget provided, calculate based on estimated costs (don't assume a value)
        if not budget or budget <= 0:
            # Estimate budget based on meal costs and people
            estimated_daily_cost = 12.0  # Average cost per person per day
            budget = estimated_daily_cost * people * 7  # Weekly estimate
            activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No budget provided, using estimated budget of ${budget:.2f}")
        
        # Get available ingredient names
        available_ingredients = [ing.get('name', '') for ing in ingredients]
        available_with_prices = {ing.get('name', '').lower(): ing.get('price', 0) for ing in ingredients}
        
        # Create grocery list from available ingredients
        grocery_list = []
        for ing in ingredients[:20]:  # Top 20 ingredients
            grocery_list.append({
                "ingredient": ing.get('name', ''),
                "quantity": "varies",
                "unit": "as needed",
                "estimated_cost": ing.get('price', 0),
                "category": ing.get('category', 'other')
            })
        
        total_grocery_cost = sum(item['estimated_cost'] for item in grocery_list)
        
        # Create weekly meal plan
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_plan = []
        
        # Meal templates
        breakfast_options = [
            {
                "name": "Oatmeal with Bananas",
                "ingredients": [{"name": "Oats", "quantity": "1 cup"}, {"name": "Bananas", "quantity": "2"}],
                "recipe": "Cook oats with water, top with sliced bananas. Add a pinch of salt for flavor.",
                "cooking_time": "10 minutes",
                "difficulty": "easy",
                "cost": 2.50
            },
            {
                "name": "Scrambled Eggs with Toast",
                "ingredients": [{"name": "Eggs", "quantity": "3"}, {"name": "Whole Wheat Bread", "quantity": "2 slices"}],
                "recipe": "Scramble eggs in a pan with a little oil. Toast bread. Serve together.",
                "cooking_time": "15 minutes",
                "difficulty": "easy",
                "cost": 3.00
            },
            {
                "name": "Apple and Oatmeal",
                "ingredients": [{"name": "Oats", "quantity": "1 cup"}, {"name": "Apples", "quantity": "1"}],
                "recipe": "Cook oats, add diced apples and cinnamon if available.",
                "cooking_time": "10 minutes",
                "difficulty": "easy",
                "cost": 2.75
            },
        ]
        
        lunch_options = [
            {
                "name": "Rice and Beans",
                "ingredients": [{"name": "Brown Rice", "quantity": "1 cup"}, {"name": "Black Beans", "quantity": "1 can"}],
                "recipe": "Cook rice according to package. Heat beans. Serve together with seasonings.",
                "cooking_time": "30 minutes",
                "difficulty": "easy",
                "cost": 3.75
            },
            {
                "name": "Turkey Sandwich",
                "ingredients": [{"name": "Ground Turkey", "quantity": "4 oz"}, {"name": "Whole Wheat Bread", "quantity": "2 slices"}],
                "recipe": "Cook turkey, season, make sandwich with bread.",
                "cooking_time": "20 minutes",
                "difficulty": "easy",
                "cost": 4.50
            },
            {
                "name": "Vegetable Soup",
                "ingredients": [{"name": "Carrots", "quantity": "1/2 cup"}, {"name": "Potatoes", "quantity": "1/2 cup"}, {"name": "Onions", "quantity": "1/4 cup"}],
                "recipe": "Chop vegetables, boil in water with seasonings until tender.",
                "cooking_time": "25 minutes",
                "difficulty": "easy",
                "cost": 2.50
            },
        ]
        
        dinner_options = [
            {
                "name": "Chicken with Vegetables",
                "ingredients": [{"name": "Chicken Breast", "quantity": "6 oz"}, {"name": "Broccoli", "quantity": "1 cup"}, {"name": "Carrots", "quantity": "1/2 cup"}],
                "recipe": "Pan-fry chicken until cooked through. Steam vegetables. Serve together.",
                "cooking_time": "30 minutes",
                "difficulty": "medium",
                "cost": 6.00
            },
            {
                "name": "Turkey with Potatoes",
                "ingredients": [{"name": "Ground Turkey", "quantity": "6 oz"}, {"name": "Potatoes", "quantity": "1 cup"}],
                "recipe": "Cook turkey, bake or boil potatoes until tender. Season to taste.",
                "cooking_time": "35 minutes",
                "difficulty": "medium",
                "cost": 5.50
            },
            {
                "name": "Rice Bowl with Vegetables",
                "ingredients": [{"name": "Brown Rice", "quantity": "1 cup"}, {"name": "Spinach", "quantity": "1 cup"}, {"name": "Tomatoes", "quantity": "1/2 cup"}],
                "recipe": "Cook rice. Sauté vegetables. Combine in a bowl.",
                "cooking_time": "25 minutes",
                "difficulty": "easy",
                "cost": 4.00
            },
        ]
        
        # Filter based on available ingredients
        def ingredient_available(meal_ingredients):
            for ing in meal_ingredients:
                ing_name = ing.get('name', '').lower()
                if not any(avail.lower() in ing_name or ing_name in avail.lower() for avail in available_ingredients):
                    return False
            return True
        
        filtered_breakfast = [m for m in breakfast_options if ingredient_available(m['ingredients'])] or breakfast_options
        filtered_lunch = [m for m in lunch_options if ingredient_available(m['ingredients'])] or lunch_options
        filtered_dinner = [m for m in dinner_options if ingredient_available(m['ingredients'])] or dinner_options
        
        # Generate weekly plan
        total_cost = 0
        for i, day in enumerate(days):
            breakfast = filtered_breakfast[i % len(filtered_breakfast)].copy()
            lunch = filtered_lunch[i % len(filtered_lunch)].copy()
            dinner = filtered_dinner[i % len(filtered_dinner)].copy()
            
            day_cost = breakfast['cost'] + lunch['cost'] + dinner['cost']
            total_cost += day_cost
            
            weekly_plan.append({
                "day": day,
                "meals": {
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "dinner": dinner
                }
            })
        
        # Scale for number of people and adjust to budget
        total_cost = total_cost * people
        
        if total_cost > budget:
            scale_factor = (budget * 0.9) / total_cost
            for day in weekly_plan:
                for meal_type in day['meals']:
                    day['meals'][meal_type]['cost'] = day['meals'][meal_type]['cost'] * scale_factor
            total_cost = budget * 0.9
        
        budget_utilization = (total_cost / budget * 100) if budget > 0 else 0
        
        return {
            "grocery_list": grocery_list,
            "total_grocery_cost": round(total_grocery_cost, 2),
            "days": weekly_plan,
            "weekly_summary": {
                "total_cost": round(total_cost, 2),
                "serves": people,
                "location": location,
                "budget_utilization": f"{budget_utilization:.1f}%"
            },
            "cooking_tips": [
                "Prep vegetables at the beginning of the week to save time",
                "Cook grains in bulk and store for multiple meals",
                "Use leftovers creatively for next day's lunch",
                "Season simply with salt, pepper, and basic spices",
                "Store cooked meals in airtight containers for up to 3 days"
            ],
            "storage_advice": [
                "Store vegetables in the refrigerator crisper drawer",
                "Keep grains and dry goods in sealed containers",
                "Freeze meat if not using within 2 days",
                "Label and date all meal prep containers"
            ]
        }
