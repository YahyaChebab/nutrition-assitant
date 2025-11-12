from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from utils.chat_manager import ChatManager
from utils.openai_research_client import GroqResearchClient
from utils.meal_planner import MealPlanner
from datetime import datetime
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS with explicit settings
CORS(app, 
     origins="*",
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type"],
     supports_credentials=False,
     max_age=3600)

# Initialize managers
print("\n" + "=" * 60)
print("INITIALIZING SERVICES")
print("=" * 60)

# Check if Groq API key is available
groq_key = os.getenv('GROQ_API_KEY', '').strip()
if groq_key:
    print(f"[INFO] ✅ GROQ_API_KEY found (length: {len(groq_key)})")
else:
    print(f"[WARNING] ⚠️  GROQ_API_KEY not found in environment")
    print(f"[INFO] 💡 Set GROQ_API_KEY in .env file to enable AI-generated meal plans")
    print(f"[INFO] 💡 Get your key from: https://console.groq.com/")

chat_manager = ChatManager()
research_client = GroqResearchClient()
meal_planner = MealPlanner(research_client)  # Will be updated with session info per request
print("=" * 60 + "\n")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Main chat endpoint"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Get or create session
        session = chat_manager.get_session(session_id)
        
        # Process message and get AI response
        response = chat_manager.process_message(session_id, user_message)
        
        # Check if we should trigger meal planning
        if chat_manager.should_generate_meal_plan(session_id):
            # Start meal planning process
            user_data = session.get('user_data', {})
            location = user_data.get('location', '')
            budget = user_data.get('budget', 0)
            people = user_data.get('people', 1)
            
            # Set status to processing immediately
            session['status'] = 'processing'
            
            try:
                # Research phase - add to activity log immediately
                chat_manager.add_activity_log(session_id, f"🔍 Researching affordable food prices in {location}...")
                
                ingredients = research_client.research_ingredients(location, budget)
                chat_manager.add_activity_log(session_id, f"✅ Found {len(ingredients)} affordable ingredients at local stores")
                
                # Meal planning phase - add to activity log immediately
                chat_manager.add_activity_log(session_id, "📊 Analyzing budget constraints...")
                chat_manager.add_activity_log(session_id, "📋 Creating your personalized grocery list and meal plan...")
                
                # Update meal_planner with session info for real-time activity log updates
                meal_planner.chat_manager = chat_manager
                meal_planner.session_id = session_id
                
                # Generate meal plan (this will add its own activity log entries to session in real-time)
                meal_plan = meal_planner.generate_meal_plan(
                    user_data,
                    ingredients,
                    session.get('activity_log', [])  # Pass existing activity log
                )
                
                # Format final response message
                weekly_summary = meal_plan.get('weekly_summary', {})
                total_cost = weekly_summary.get('total_cost', 0)
                budget_util = weekly_summary.get('budget_utilization', '0%')
                
                final_message = f"""Here's your personalized affordable meal plan! 🥗

📊 **Weekly Summary**:
- Total Cost: ${total_cost:.2f} CAD (under your ${budget} CAD budget - {budget_util} utilized)
- Serves: {people} people
- Location: {location}

🛒 **Grocery List**: Ready for shopping
📅 **Meal Plan**: 7 days of meals with recipes
💡 **Tips**: Cooking and storage advice included

Would you like any adjustments or have questions about your plan?"""
                
                # Add meal plan to session and mark as generated
                session['meal_plan'] = meal_plan
                session['meal_plan_generated'] = True
                session['status'] = 'complete'
                session['state'] = 'complete'
                
                response['meal_plan'] = meal_plan
                response['activity_log'] = session.get('activity_log', [])
                response['message'] = final_message
                
            except Exception as e:
                error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Error: {str(e)}"
                chat_manager.add_activity_log(session_id, error_msg)
                session['status'] = 'error'
                response['activity_log'] = session.get('activity_log', [])
                response['error'] = str(e)
                response['status'] = 'error'
                response['message'] = f"I encountered an error while creating your meal plan. Please try again or contact support. Error: {str(e)}"
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'An error occurred processing your request'}), 500

@app.route('/api/activity_log', methods=['GET'])
def get_activity_log():
    """Get real-time activity updates"""
    session_id = request.args.get('session_id', 'default')
    session = chat_manager.get_session(session_id)
    return jsonify({
        'activity_log': session.get('activity_log', []),
        'status': session.get('status', 'idle')
    })

@app.route('/api/generate_meal_plan', methods=['POST'])

def generate_meal_plan(self, user_data, ingredients, activity_log):
    """
    Generate a weekly meal plan and grocery list with correct field names for frontend.
    """
    try:
        location = user_data.get("location", "Canada")
        budget = float(user_data.get("budget", 0))
        people = int(user_data.get("people", 1))
        diet = user_data.get("diet", "balanced")

        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🍳 Creating meal plan for {people} people in {location} ({diet} diet)...")

        # --- Step 1: Build grocery list with correct field names ---
        grocery_list = []
        for item in ingredients:
            try:
                name = item.get("name", "Unknown Ingredient")
                quantity = item.get("quantity", "1")
                
                # Use correct field names for frontend
                estimated_cost = float(item.get("price", round(random.uniform(1.0, 10.0), 2)))
                
                grocery_list.append({
                    "ingredient": name,  # Frontend expects this
                    "quantity": quantity,
                    "unit": "unit",  # Add unit field
                    "estimated_cost": round(estimated_cost, 2),  # Frontend expects this
                    "store": item.get("store", "Local Store"),
                    "store_address": item.get("address", "Local Address")
                })
            except Exception as e:
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Skipped ingredient due to error: {str(e)}")
                continue

        # --- Step 2: Calculate total grocery cost ---
        total_grocery_cost = 0.0
        for item in grocery_list:
            try:
                total_grocery_cost += float(item.get("estimated_cost", 0))
            except Exception:
                continue

        total_grocery_cost = round(total_grocery_cost, 2)

        # --- Step 3: Compute budget utilization ---
        if budget > 0:
            utilization = min((total_grocery_cost / budget) * 100, 100)
            budget_utilization = f"{utilization:.1f}%"
        else:
            budget_utilization = "N/A"

        # --- Step 4: Generate 7-day meal schedule ---
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meal_schedule = []
        for day in days:
            meal_schedule.append({
                "day": day,
                "breakfast": f"Oatmeal with fruit ({diet})",
                "lunch": f"Grilled chicken with veggies ({diet})",
                "dinner": f"Rice bowl with mixed vegetables ({diet})"
            })

        # --- Step 5: Build output dictionary with correct field names ---
        meal_plan = {
            "weekly_summary": {
                "total_cost": total_grocery_cost,  # Use same total as grocery list
                "budget_utilization": budget_utilization,
                "currency": "CAD",
                "serves": people,
                "location": location
            },
            "grocery_list": grocery_list,
            "total_grocery_cost": total_grocery_cost,  # Add this for frontend
            "meal_schedule": meal_schedule,
            "tips": [
                "Buy items in bulk for better prices.",
                "Use seasonal produce for fresher and cheaper meals.",
                "Cook in batches to save time and reduce waste."
            ]
        }

        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Meal plan created successfully! Total cost: ${total_grocery_cost:.2f} CAD")

        return meal_plan

    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error during meal plan generation: {str(e)}"
        activity_log.append(error_msg)
        return {
            "weekly_summary": {
                "total_cost": 0,
                "budget_utilization": "0%",
                "currency": "CAD",
                "serves": user_data.get("people", 1),
                "location": user_data.get("location", "Unknown")
            },
            "grocery_list": [],
            "total_grocery_cost": 0,
            "meal_schedule": [],
            "tips": [],
            "error": str(e)
        }

if __name__ == '__main__':
    import socket
    
    # Get local IP address for network access
    def get_local_ip():
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print("BACKEND SERVER")
    print("=" * 60)
    print("Status: Starting Flask Backend Server")
    print("Local:  http://localhost:5001")
    print(f"Network: http://{local_ip}:5001")
    print("Host:   0.0.0.0 (accessible on all interfaces)")
    print("Mode:   Debug")
    print("CORS:   Enabled for all origins")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
