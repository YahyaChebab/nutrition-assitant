import openai
import os
from typing import Dict, List
from datetime import datetime

class ChatManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = openai.OpenAI(api_key=api_key) if api_key else None
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true' or not api_key
    
    def get_session(self, session_id: str) -> Dict:
        """Get or create a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'state': 'welcome',
                'user_data': {},
                'conversation_history': [],
                'activity_log': [],
                'status': 'idle'
            }
        return self.sessions[session_id]
    
    def add_activity_log(self, session_id: str, message: str):
        """Add timestamped activity log entry"""
        session = self.get_session(session_id)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        session['activity_log'].append(log_entry)
        return log_entry
    
    def process_message(self, session_id: str, user_message: str) -> Dict:
        """Process user message and return AI response"""
        session = self.get_session(session_id)
        state = session['state']
        user_data = session.get('user_data', {})
        
        # Add user message to history
        session['conversation_history'].append({'role': 'user', 'content': user_message})
        
        # Handle initial greeting
        if state == 'welcome' and user_message.lower() in ['get started', 'start', 'hello', 'hi', 'begin']:
            session['state'] = 'collecting_info'
            welcome_message = """Welcome to NutriBudget AI! 🍎

I'm here to help you create a personalized, affordable meal plan tailored to your family's needs and budget.

To get started, I'll need the following information:

**1. Household Size**
   How many people are you feeding?

**2. Weekly Budget**
   What's your weekly food budget? (Please specify the amount, e.g., "$100" or "100 CAD")

**3. Location**
   Which city are you shopping in? (This helps me find the best local prices)

**4. Dietary Restrictions & Preferences**
   Any allergies, dietary restrictions, or food preferences? (e.g., "vegetarian", "no shellfish", "prefer chicken")

Please provide all this information in your response, and I'll create a customized meal plan just for you!"""
            
            response = {
                'message': welcome_message,
                'state': 'collecting_info',
                'user_data': user_data
            }
            session['conversation_history'].append({'role': 'assistant', 'content': welcome_message})
            return response
        
        # Extract all information from user message
        if state == 'collecting_info':
            extracted_data = self._extract_user_data(user_message, user_data)
            
            # Check what's missing
            missing_fields = self._check_missing_fields(extracted_data)
            
            if missing_fields:
                # Ask for missing information with helpful context
                missing_text = ", ".join(missing_fields)
                if len(missing_fields) == 1:
                    field = missing_fields[0]
                    # Use dynamic prompt with static fallback
                    prompt_message = self._get_dynamic_prompt(field, extracted_data, session.get('conversation_history', []))
                    response = {
                        'message': prompt_message,
                        'state': 'collecting_info',
                        'user_data': extracted_data
                    }
                else:
                    response = {
                        'message': f"I'm still missing: {missing_text}. Could you provide these details?",
                        'state': 'collecting_info',
                        'user_data': extracted_data
                    }
            else:
                # All info collected, show confirmation
                # Double-check that budget is actually provided (not just a number)
                if not extracted_data.get('budget'):
                    # Use dynamic prompt with static fallback
                    prompt_message = self._get_dynamic_prompt('Weekly budget', extracted_data, session.get('conversation_history', []))
                    response = {
                        'message': prompt_message,
                        'state': 'collecting_info',
                        'user_data': extracted_data
                    }
                else:
                    session['user_data'] = extracted_data
                    session['state'] = 'confirm'
                    response = self._generate_confirmation(extracted_data)
                    response['state'] = 'confirm'
            
            session['user_data'] = extracted_data
            return response
        
        # Handle confirmation
        elif state == 'confirm':
            if user_message.lower() in ['yes', 'y', 'correct', 'yeah', 'sure', 'ok', 'okay', 'confirmed']:
                session['state'] = 'processing'
                self.add_activity_log(session_id, "🤖 Collecting user preferences... ✓")
                
                response = {
                    'message': "Perfect! Let me research the best affordable ingredients in your area and create your personalized meal plan. This will take just a moment...",
                    'state': 'processing',
                    'user_data': user_data,
                    'ready_for_meal_plan': True
                }
            elif user_message.lower() in ['no', 'n', 'incorrect', 'wrong', 'change']:
                # Reset to collecting info
                session['state'] = 'collecting_info'
                session['user_data'] = {}
                response = {
                    'message': "No problem! Let's start over. Please provide:\n\n1. **Household Size** - How many people?\n2. **Weekly Budget** - Amount (e.g., $100)\n3. **Location** - Which city?\n4. **Dietary Restrictions/Preferences** - Any allergies or preferences?",
                    'state': 'collecting_info',
                    'user_data': {},
                    'reset': True
                }
            else:
                # Ask for clarification
                response = {
                    'message': "Please confirm: Is the information correct? (Yes/No)",
                    'state': 'confirm',
                    'user_data': user_data
                }
        
        else:
            # Use GPT for general conversation or corrections
            response = self._get_gpt_response(session['conversation_history'], user_data)
            response['state'] = state
            response['user_data'] = user_data
        
        session['conversation_history'].append({'role': 'assistant', 'content': response['message']})
        return response
    
    def _extract_user_data(self, text: str, existing_data: Dict) -> Dict:
        """Extract all user data from text"""
        import re
        
        data = existing_data.copy()
        text_lower = text.lower()
        text_original = text
        
        # Extract household size FIRST (to avoid confusion with budget)
        # Look for explicit patterns with "people", "person", "household"
        people_patterns = [
            r'(\d+)\s*(?:people|person|persons|household|members)',
            r'(?:household|family|feeding|serving).*?(\d+)',
            r'(\d+)\s*(?:people|person)',
        ]
        for pattern in people_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                num = int(matches[0])
                if 1 <= num <= 20:  # Reasonable household size
                    data['people'] = num
                    break
        
        # Extract budget - ONLY when explicitly mentioned
        # Be very strict to avoid extracting random numbers
        budget_found = False
        
        # Pattern 1: Explicit budget mentions with dollar amounts
        budget_explicit = re.search(r'budget.*?\$?\s*(\d+(?:\.\d{2})?)\s*(?:cad|usd|dollar|dollars|per week|weekly|a week)?', text_lower)
        if budget_explicit:
            budget_value = float(budget_explicit.group(1))
            if 10 <= budget_value <= 10000:
                data['budget'] = budget_value
                budget_found = True
        
        # Pattern 2: Dollar sign with number (only if "budget" keyword is nearby)
        if not budget_found:
            # Check if "budget" appears near a dollar amount
            budget_near_dollar = re.search(r'(?:budget|spend|afford).*?\$(\d+(?:\.\d{2})?)', text_lower)
            if budget_near_dollar:
                budget_value = float(budget_near_dollar.group(1))
                if 10 <= budget_value <= 10000:
                    data['budget'] = budget_value
                    budget_found = True
        
        # Pattern 3: Dollar sign at start of sentence or after budget keywords
        if not budget_found:
            # Look for "$X" pattern but only if it's clearly a budget context
            dollar_pattern = re.search(r'\$(\d+(?:\.\d{2})?)\s*(?:cad|usd|per week|weekly|a week|budget)?', text_lower)
            if dollar_pattern:
                # Additional check: must have budget context words nearby
                budget_context_words = ['budget', 'spend', 'afford', 'cost', 'weekly', 'week']
                text_before = text_lower[max(0, dollar_pattern.start()-20):dollar_pattern.start()]
                text_after = text_lower[dollar_pattern.end():min(len(text_lower), dollar_pattern.end()+20)]
                context_text = text_before + text_after
                if any(word in context_text for word in budget_context_words):
                    budget_value = float(dollar_pattern.group(1))
                    if 10 <= budget_value <= 10000:
                        data['budget'] = budget_value
                        budget_found = True
        
        # Pattern 4: Number with currency or time period (only with explicit budget context)
        if not budget_found:
            # "100 CAD" or "100 dollars" but only if "budget" is mentioned
            if 'budget' in text_lower:
                currency_pattern = re.search(r'(\d+(?:\.\d{2})?)\s*(?:cad|usd|dollar|dollars)', text_lower)
                if currency_pattern:
                    budget_value = float(currency_pattern.group(1))
                    if 10 <= budget_value <= 10000:
                        data['budget'] = budget_value
                        budget_found = True
        
        # Extract location (city name)
        # Common patterns: "in {city}", "location: {city}", "{city}", "shopping in {city}"
        location_patterns = [
            r'(?:in|at|location:?|shopping in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:city|area)',
        ]
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Filter out common words that aren't cities
                city = matches[0].strip()
                if city.lower() not in ['the', 'and', 'or', 'for', 'with']:
                    data['location'] = city
                    break
        
        # If no location found with pattern, try to find capitalized words (likely city names)
        if not data.get('location'):
            words = text.split()
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 2:
                    # Check if it's likely a city (not at start of sentence, not common word)
                    if i > 0 and word.lower() not in ['i', 'the', 'and', 'or', 'for', 'with', 'no', 'none']:
                        data['location'] = word
                        break
        
        # Extract dietary preferences and restrictions
        dietary_keywords = {
            'vegetarian': ['vegetarian', 'veggie'],
            'vegan': ['vegan'],
            'gluten-free': ['gluten-free', 'gluten free', 'celiac'],
            'lactose-intolerant': ['lactose', 'dairy-free', 'dairy free'],
            'nut-free': ['nut-free', 'nut free', 'peanut'],
            'halal': ['halal'],
            'kosher': ['kosher'],
            'pescatarian': ['pescatarian', 'pescetarian'],
        }
        
        restrictions = data.get('dietary_restrictions', [])
        preferences = data.get('preferences', '')
        
        for restriction, keywords in dietary_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                if restriction not in restrictions:
                    restrictions.append(restriction)
        
        data['dietary_restrictions'] = restrictions
        
        # Extract food preferences (favorites, likes)
        preference_patterns = [
            r'(?:like|love|prefer|favorite|favourite)\s+(.+?)(?:\.|,|$)',
            r'prefer\s+(.+?)\s+over',
        ]
        for pattern in preference_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                preferences += ' ' + matches[0]
        
        if preferences.strip():
            data['preferences'] = preferences.strip()
        elif 'prefer' in text_lower or 'like' in text_lower or 'favorite' in text_lower:
            # User mentioned preferences but we couldn't extract, keep existing or mark as present
            if not data.get('preferences'):
                data['preferences'] = text  # Store full text as fallback
        
        # Handle "none" or "no" responses
        if 'no preferences' in text_lower or 'no dietary' in text_lower or ('no' in text_lower and 'allergies' in text_lower):
            if not data.get('dietary_restrictions'):
                data['dietary_restrictions'] = []
            if not data.get('preferences'):
                data['preferences'] = ''
        
        return data
    
    def _check_missing_fields(self, user_data: Dict) -> List[str]:
        """Check which required fields are missing"""
        required_fields = {
            'people': 'Household size',
            'budget': 'Weekly budget',
            'location': 'Location'
        }
        
        missing = []
        for field, label in required_fields.items():
            if not user_data.get(field):
                missing.append(label)
        
        return missing
    
    def _generate_confirmation(self, user_data: Dict) -> Dict:
        """Generate confirmation message"""
        people = user_data.get('people')
        budget = user_data.get('budget')
        location = user_data.get('location')
        dietary = user_data.get('dietary_restrictions', [])
        preferences = user_data.get('preferences', '')
        
        dietary_str = ', '.join(dietary) if dietary else 'None'
        preferences_str = preferences if preferences and preferences.lower() not in ['none', 'no', 'n/a', ''] else 'None'
        
        message = "Just to confirm your information:\n\n"
        
        if people:
            message += f"👨‍👩‍👧‍👦 **Household Size**: {people} people\n"
        else:
            message += f"👨‍👩‍👧‍👦 **Household Size**: Not provided\n"
        
        if budget and isinstance(budget, (int, float)):
            message += f"💰 **Weekly Budget**: ${budget:.2f} CAD\n"
        else:
            message += f"💰 **Weekly Budget**: Not provided\n"
        
        if location:
            message += f"📍 **Location**: {location}\n"
        else:
            message += f"📍 **Location**: Not provided\n"
        
        message += f"🥗 **Dietary Restrictions**: {dietary_str}\n"
        message += f"🍽️ **Preferences**: {preferences_str}\n\n"
        message += "Is this information correct? (Yes/No)"
        
        return {'message': message, 'user_data': user_data}
    
    def should_generate_meal_plan(self, session_id: str) -> bool:
        """Check if meal plan should be generated"""
        session = self.get_session(session_id)
        user_data = session.get('user_data', {})
        return (session.get('state') == 'processing' and 
                user_data.get('budget') and 
                user_data.get('people') and 
                user_data.get('location') and
                not session.get('meal_plan_generated', False))
    
    def _get_dynamic_prompt(self, field_name: str, user_data: Dict, conversation_history: List[Dict]) -> str:
        """Generate dynamic prompt for missing field using API, with static fallback"""
        # Static fallback prompts
        static_prompts = {
            'Weekly budget': "I need your weekly food budget. Please provide the amount (e.g., \"$100\" or \"100 CAD\" or \"my budget is $75 per week\").",
            'Household size': "How many people are you feeding? Please provide a number (e.g., \"4 people\" or \"feeding 4\").",
            'Location': "Which city are you shopping in? Please provide your location (e.g., \"Toronto\" or \"I'm in Chicago\")."
        }
        
        # If no API key or test mode, use static version
        if self.test_mode or not self.openai_client:
            return static_prompts.get(field_name, f"I need your {field_name.lower()}. Could you provide that information?")
        
        try:
            # Build context about what we already know
            context_parts = []
            if user_data.get('people'):
                context_parts.append(f"Household size: {user_data.get('people')} people")
            if user_data.get('budget'):
                context_parts.append(f"Budget: ${user_data.get('budget')} CAD")
            if user_data.get('location'):
                context_parts.append(f"Location: {user_data.get('location')}")
            
            context = ". ".join(context_parts) if context_parts else "No information collected yet."
            
            system_message = """You are NutriBudget AI, a helpful nutrition assistant. Generate a friendly, natural prompt asking for missing information. 
Keep it concise (1-2 sentences), friendly, and include helpful examples. Return only the prompt text, no additional explanation."""
            
            user_prompt = f"""The user is creating a meal plan. So far I know: {context}

I need to ask for: {field_name}

Generate a friendly, conversational prompt asking for this information. Include 1-2 examples of how they might respond. Keep it warm and helpful."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            dynamic_prompt = response.choices[0].message.content.strip()
            # Remove quotes if the API wrapped it in quotes
            if dynamic_prompt.startswith('"') and dynamic_prompt.endswith('"'):
                dynamic_prompt = dynamic_prompt[1:-1]
            elif dynamic_prompt.startswith("'") and dynamic_prompt.endswith("'"):
                dynamic_prompt = dynamic_prompt[1:-1]
            
            return dynamic_prompt
        except Exception as e:
            # Fallback to static on any error
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error generating dynamic prompt: {e}, using static fallback")
            return static_prompts.get(field_name, f"I need your {field_name.lower()}. Could you provide that information?")
    
    def _get_gpt_response(self, conversation_history: List[Dict], user_data: Dict) -> Dict:
        """Get GPT response for general conversation"""
        # If no API key or test mode, return helpful response
        if self.test_mode or not self.openai_client:
            return {
                'message': "I'm here to help you create an affordable meal plan! Please provide:\n1. Household size\n2. Weekly budget\n3. Food preferences/allergies\n4. Location"
            }
        
        try:
            system_message = """You are NutriBudget AI, a helpful nutrition assistant helping families create affordable meal plans. 
Be friendly, empathetic, and practical. Guide users to provide: household size, weekly budget, dietary restrictions, and location."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    *conversation_history[-10:]  # Last 10 messages for context
                ],
                max_tokens=200,
                temperature=0.7
            )
            return {'message': response.choices[0].message.content}
        except Exception as e:
            return {'message': f"I apologize, but I'm having trouble processing that. Could you try again?"}
