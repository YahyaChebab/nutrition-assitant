from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from utils.chat_manager import ChatManager
from utils.perplexity_client import PerplexityClient
from utils.meal_planner import MealPlanner
from datetime import datetime

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
chat_manager = ChatManager()
perplexity_client = PerplexityClient()
meal_planner = MealPlanner(perplexity_client)


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
            activity_log = []
            user_data = session.get('user_data', {})
            location = user_data.get('location', '')
            budget = user_data.get('budget', 0)
            people = user_data.get('people', 1)
            
            try:
                # Research phase
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Researching affordable food prices in {location}...")
                chat_manager.add_activity_log(session_id, f"🔍 Researching affordable food prices in {location}...")
                
                ingredients = perplexity_client.research_ingredients(location, budget)
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Found {len(ingredients)} affordable ingredients at local stores")
                chat_manager.add_activity_log(session_id, f"✅ Found {len(ingredients)} affordable ingredients at local stores")
                
                # Meal planning phase
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Analyzing budget constraints...")
                chat_manager.add_activity_log(session_id, "📊 Analyzing budget constraints...")
                
                activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Creating your personalized grocery list and meal plan...")
                chat_manager.add_activity_log(session_id, "📋 Creating your personalized grocery list and meal plan...")
                
                meal_plan = meal_planner.generate_meal_plan(
                    user_data,
                    ingredients,
                    activity_log
                )
                
                # Add all activity log entries to session
                session['activity_log'].extend(activity_log)
                
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
                activity_log.append(error_msg)
                session['activity_log'] = activity_log
                session['status'] = 'error'
                response['activity_log'] = activity_log
                response['error'] = str(e)
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
def generate_meal_plan():
    """Trigger meal plan generation"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        session = chat_manager.get_session(session_id)
        user_data = session.get('user_data', {})
        
        if not user_data:
            return jsonify({'error': 'User data not collected'}), 400
        
        activity_log = []
        location = user_data.get('location', '')
        budget = user_data.get('budget', 0)
        
        # Research ingredients
        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Researching cheapest foods in {location}...")
        ingredients = perplexity_client.research_ingredients(location, budget)
        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Found {len(ingredients)} affordable ingredients")
        
        # Generate meal plan
        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Generating meal plan...")
        meal_plan = meal_planner.generate_meal_plan(user_data, ingredients, activity_log)
        activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Meal plan ready!")
        
        session['meal_plan'] = meal_plan
        session['activity_log'] = activity_log
        
        return jsonify({
            'meal_plan': meal_plan,
            'activity_log': activity_log
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("BACKEND SERVER")
    print("=" * 60)
    print("Status: Starting Flask Backend Server")
    print("URL:    http://localhost:5001")
    print("Host:   127.0.0.1")
    print("Mode:   Debug")
    print("CORS:   Enabled for all origins")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5001, host='127.0.0.1')
