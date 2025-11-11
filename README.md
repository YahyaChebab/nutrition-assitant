# AI Nutrition Assistant

A web application that helps low-income families create affordable, healthy meal plans using AI. The app features a conversational chat interface that collects user information, researches local food prices, and generates personalized meal plans.

## Features

- 🤖 Conversational AI interface for data collection
- 🔍 Real-time research of local food prices using Perplexity API
- 📋 Personalized meal plan generation using GPT-4
- ✅ Recipe validation and hallucination detection
- 📊 Real-time activity logging
- 💰 Budget enforcement and cost calculations

## Tech Stack

- **Frontend**: Next.js 16 with TypeScript
- **Backend**: Python Flask
- **AI APIs**: OpenAI GPT-4 + Perplexity API
- **Styling**: Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.x
- Node.js and npm
- OpenAI API Key (optional, for AI features)
- Perplexity API Key (optional, for price research)

### Running the Application

1. **Install dependencies and start both servers** (recommended):

```bash
./start.sh
```

This script will:

- Install backend Python dependencies
- Install frontend npm dependencies
- Start both backend and frontend servers simultaneously

The application will be available at:

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001

Press `Ctrl+C` to stop both servers.

### Manual Setup (Alternative)

If you prefer to run servers manually:

#### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file in the backend directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

4. Run the Flask server:

```bash
python app.py
```

The backend will run on `http://localhost:5001`

#### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Run the development server:

```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Run the start script:

   ```bash
   ./start.sh
   ```

2. Navigate to `http://localhost:3000` in your browser

3. Click "Get Started" to begin the conversation

4. Follow the prompts to provide:

   - **Household Size**: Number of people you're feeding
   - **Weekly Budget**: Your food budget (e.g., "$100" or "100 CAD")
   - **Location**: City where you're shopping
   - **Dietary Restrictions**: Any allergies or dietary restrictions
   - **Food Preferences**: Favorite foods or preferences

5. Confirm your information

6. Wait for the AI to research ingredients and generate your personalized meal plan

## Notes

- The app works without API keys using mock data for testing
- For full functionality, add your API keys to `backend/.env`
- Both servers must be running for the app to work properly
- Use the `start.sh` script for the easiest setup and launch experience

## Project Structure

```
myUFV/
├── start.sh                    # Start script for both servers
├── backend/
│   ├── app.py                  # Flask backend server
│   ├── requirements.txt        # Python dependencies
│   └── utils/
│       ├── chat_manager.py     # Conversation management
│       ├── perplexity_client.py # Perplexity API integration
│       └── meal_planner.py     # Meal plan generation
├── frontend/
│   ├── app/
│   │   └── page.tsx            # Main application page
│   └── package.json            # Node.js dependencies
└── README.md
```

## API Endpoints

- `POST /api/chat` - Main chat endpoint for conversation
- `GET /api/activity_log` - Get real-time activity updates
- `POST /api/generate_meal_plan` - Trigger meal plan generation
- `GET /api/health` - Health check endpoint

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4 (optional)
- `PERPLEXITY_API_KEY` - Your Perplexity API key for research (optional)

Note: The app works without API keys using mock data for testing purposes.

## License

MIT
