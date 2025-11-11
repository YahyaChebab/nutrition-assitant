#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 AI Nutrition Assistant${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Install backend dependencies
echo -e "${YELLOW}📦 Checking backend dependencies...${NC}"
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend dependencies ready${NC}"
    else
        # Try without --quiet to see errors
        pip3 install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to install backend dependencies${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}❌ requirements.txt not found in backend directory${NC}"
    exit 1
fi
cd ..

# Install frontend dependencies
echo -e "${YELLOW}📦 Checking frontend dependencies...${NC}"
cd frontend
if [ -f "package.json" ]; then
    if [ ! -d "node_modules" ]; then
        npm install --silent
    else
        # Check if node_modules is complete by checking for a key dependency
        if [ ! -d "node_modules/next" ]; then
            npm install --silent
        fi
    fi
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend dependencies ready${NC}"
    else
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ package.json not found in frontend directory${NC}"
    exit 1
fi
cd ..

echo -e "\n${BLUE}========================================${NC}"
echo -e "${YELLOW}🛑 Stopping any existing servers...${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Kill any existing backend processes
echo -e "${YELLOW}Checking for existing backend processes...${NC}"
BACKEND_PIDS=$(lsof -ti:5001 2>/dev/null)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}Terminating existing backend processes on port 5001...${NC}"
    kill -9 $BACKEND_PIDS 2>/dev/null
    sleep 1
fi

# Also check for python processes running app.py
PYTHON_PIDS=$(ps aux | grep '[p]ython3.*app.py' | awk '{print $2}')
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "${YELLOW}Terminating existing Python app.py processes...${NC}"
    kill -9 $PYTHON_PIDS 2>/dev/null
    sleep 1
fi

# Kill any existing frontend processes
echo -e "${YELLOW}Checking for existing frontend processes...${NC}"
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}Terminating existing frontend processes on port 3000...${NC}"
    kill -9 $FRONTEND_PIDS 2>/dev/null
    sleep 1
fi

# Also check for node processes running next dev
NODE_PIDS=$(ps aux | grep '[n]ode.*next dev' | awk '{print $2}')
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${YELLOW}Terminating existing Next.js processes...${NC}"
    kill -9 $NODE_PIDS 2>/dev/null
    sleep 1
fi

# Clean up Next.js lock files
if [ -f "frontend/.next/dev/lock" ]; then
    echo -e "${YELLOW}Removing Next.js lock file...${NC}"
    rm -f frontend/.next/dev/lock 2>/dev/null
fi

# Clean up .next directory if it exists and is causing issues
if [ -d "frontend/.next" ]; then
    echo -e "${YELLOW}Cleaning up Next.js cache...${NC}"
    rm -rf frontend/.next 2>/dev/null
fi

sleep 1

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting servers...${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Start backend server in background
echo -e "${GREEN}📦 Starting backend server on http://localhost:5001...${NC}"
(
    cd backend
    python3 app.py
) &
BACKEND_PID=$!

# Start frontend server in background
echo -e "${GREEN}🎨 Starting frontend server on http://localhost:3000...${NC}"
(
    cd frontend
    npm run dev
) &
FRONTEND_PID=$!

# Wait a moment for servers to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check for errors above.${NC}"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start. Check for errors above.${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Both servers are running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Frontend: ${NC}http://localhost:3000"
echo -e "${GREEN}Backend:  ${NC}http://localhost:5001"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Wait for both processes and show their output
wait $BACKEND_PID $FRONTEND_PID
