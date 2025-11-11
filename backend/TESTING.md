# Testing Without API Keys

The application can be tested **without any API keys**! The backend automatically uses mock data and fallback meal plans when API keys are not available.

## Quick Test

### Option 1: Run Test Server (Recommended)

```bash
cd backend
python test_server.py
```

This will start the server in test mode, which uses:
- Mock ingredient data (no Perplexity API needed)
- Fallback meal plans (no OpenAI API needed)
- Rule-based conversation flow (works without APIs)

### Option 2: Run Normal Server Without Keys

```bash
cd backend
python app.py
```

If no API keys are set, the app will automatically:
- Use mock ingredients from `perplexity_client.py`
- Use fallback meal plans from `meal_planner.py`
- Work perfectly for testing!

## What Works Without API Keys

✅ **Full conversation flow** - Collecting budget, people, location, dietary restrictions, preferences
✅ **Data collection and confirmation** - All rule-based, no API needed
✅ **Mock ingredient research** - Returns 15+ affordable ingredients
✅ **Fallback meal plans** - Generates full weekly meal plans using available ingredients
✅ **Activity logging** - Shows progress during meal plan generation
✅ **Meal plan display** - Shows recipes, ingredients, and costs

## What Requires API Keys

❌ **Real ingredient research** - Perplexity API for actual local prices
❌ **GPT-4 meal plans** - OpenAI API for AI-generated meal plans
❌ **General conversation** - GPT-4 for handling unexpected user messages

## Test the Full Flow

1. **Start backend** (with or without API keys):
   ```bash
   cd backend
   python app.py
   # or
   python test_server.py
   ```

2. **Start frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the conversation**:
   - Click "Get Started"
   - Enter budget: `$75`
   - Enter people: `4`
   - Enter location: `Chicago`
   - Enter dietary restrictions: `none` or `lactose intolerant`
   - Enter preferences: `none` or `prefer chicken`
   - Confirm: `yes`
   - Wait for meal plan generation

4. **Expected Result**:
   - Activity log shows research and generation steps
   - Meal plan appears with recipes for the week
   - All using mock/fallback data if no API keys

## Environment Variables (Optional)

Create a `.env` file in the `backend` directory:

```env
# Optional - only needed for real API calls
OPENAI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# Optional - force test mode
TEST_MODE=true
```

## Mock Data

The app includes comprehensive mock data:
- **15+ mock ingredients** with prices and stores
- **Weekly meal plans** with breakfast, lunch, and dinner
- **Recipe validation** using available ingredients
- **Budget calculations** based on user input

## Troubleshooting

**Backend won't start?**
- Make sure you're in the `backend` directory
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.8+)

**Frontend can't connect?**
- Make sure backend is running on port 5000
- Check browser console for errors
- Verify CORS is enabled (it is by default)

**No meal plan generated?**
- Check backend console for errors
- Verify all user data was collected
- Check activity log in the frontend

## Next Steps

Once testing works, you can:
1. Get OpenAI API key from https://platform.openai.com/
2. Get Perplexity API key from https://www.perplexity.ai/
3. Add keys to `.env` file for real API integration
4. Test with real ingredient research and AI meal plans

The app works great in test mode for development and testing! 🚀


