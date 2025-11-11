# AI Nutrition Assistant Backend

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

3. Run the Flask server:
```bash
python app.py
```

The server will run on `http://localhost:5000`

## API Endpoints

- `POST /api/chat` - Main chat endpoint for conversation
- `GET /api/activity_log` - Get real-time activity updates
- `POST /api/generate_meal_plan` - Trigger meal plan generation

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4
- `PERPLEXITY_API_KEY` - Your Perplexity API key for research

