#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}[SHUTDOWN] Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}[BACKEND] Stopping server (PID: $BACKEND_PID)${NC}"
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}[FRONTEND] Stopping server (PID: $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}[SHUTDOWN] Servers stopped${NC}"
    exit
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Nutrition Assistant${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Install backend dependencies
echo -e "${YELLOW}[BACKEND] Checking dependencies...${NC}"
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[BACKEND] Dependencies ready${NC}"
    else
        # Try without --quiet to see errors
        pip3 install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}[BACKEND] Failed to install dependencies${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}[BACKEND] requirements.txt not found${NC}"
    exit 1
fi
cd ..

# Install frontend dependencies
echo -e "${YELLOW}[FRONTEND] Checking dependencies...${NC}"
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
        echo -e "${GREEN}[FRONTEND] Dependencies ready${NC}"
    else
        echo -e "${RED}[FRONTEND] Failed to install dependencies${NC}"
        exit 1
    fi
else
    echo -e "${RED}[FRONTEND] package.json not found${NC}"
    exit 1
fi
cd ..

echo -e "\n${BLUE}========================================${NC}"
echo -e "${YELLOW}[CLEANUP] Stopping any existing servers...${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Kill any existing backend processes
echo -e "${YELLOW}[BACKEND] Checking for existing processes...${NC}"

# Check for processes on port 5001
if command -v lsof &> /dev/null; then
    BACKEND_PIDS=$(lsof -ti:5001 2>/dev/null)
    if [ ! -z "$BACKEND_PIDS" ]; then
        echo -e "${YELLOW}[BACKEND] Terminating processes on port 5001${NC}"
        kill -9 $BACKEND_PIDS 2>/dev/null
        sleep 1
    fi
fi

# Check for python processes running app.py (more reliable)
if command -v pgrep &> /dev/null; then
    PYTHON_PIDS=$(pgrep -f "python3.*app.py" 2>/dev/null)
else
    # Fallback to ps and grep
    PYTHON_PIDS=$(ps aux | grep -E "[p]ython3.*app.py" | awk '{print $2}' | tr '\n' ' ')
fi
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "${YELLOW}[BACKEND] Terminating Python processes (PIDs: $PYTHON_PIDS)${NC}"
    kill -9 $PYTHON_PIDS 2>/dev/null
    sleep 1
fi

# Kill any existing frontend processes
echo -e "${YELLOW}[FRONTEND] Checking for existing processes...${NC}"

# Check for processes on port 3000
if command -v lsof &> /dev/null; then
    FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo -e "${YELLOW}[FRONTEND] Terminating processes on port 3000${NC}"
        kill -9 $FRONTEND_PIDS 2>/dev/null
        sleep 1
    fi
fi

# Check for node processes running next dev (more reliable)
if command -v pgrep &> /dev/null; then
    NODE_PIDS=$(pgrep -f "next dev" 2>/dev/null)
else
    # Fallback to ps and grep
    NODE_PIDS=$(ps aux | grep -E "[n]ode.*next dev" | awk '{print $2}' | tr '\n' ' ')
fi
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${YELLOW}[FRONTEND] Terminating Next.js processes (PIDs: $NODE_PIDS)${NC}"
    kill -9 $NODE_PIDS 2>/dev/null
    sleep 1
fi

# Clean up Next.js lock files
if [ -f "frontend/.next/dev/lock" ]; then
    echo -e "${YELLOW}[FRONTEND] Removing lock file${NC}"
    rm -f frontend/.next/dev/lock 2>/dev/null
fi

# Also check for any Next.js processes more broadly
if command -v pgrep &> /dev/null; then
    NEXTJS_PIDS=$(pgrep -f "next-server" 2>/dev/null)
else
    # Fallback to ps and grep
    NEXTJS_PIDS=$(ps aux | grep -E "[n]ext-server" | awk '{print $2}' | tr '\n' ' ')
fi
if [ ! -z "$NEXTJS_PIDS" ]; then
    echo -e "${YELLOW}[FRONTEND] Terminating Next.js server processes (PIDs: $NEXTJS_PIDS)${NC}"
    kill -9 $NEXTJS_PIDS 2>/dev/null
    sleep 1
fi

sleep 1

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}[STARTUP] Starting servers...${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Start backend server in background
echo -e "${GREEN}[BACKEND] Starting server...${NC}"
echo -e "${BLUE}  URL:    http://localhost:5001${NC}"
echo -e "${BLUE}  Status: Starting...${NC}\n"
(
    cd backend
    python3 app.py 2>&1 | sed 's/^/[BACKEND] /'
) &
BACKEND_PID=$!

# Start frontend server in background
echo -e "${GREEN}[FRONTEND] Starting server...${NC}"
echo -e "${BLUE}  URL:    http://localhost:3000${NC}"
echo -e "${BLUE}  Status: Starting...${NC}\n"
(
    cd frontend
    npm run dev 2>&1 | sed 's/^/[FRONTEND] /'
) &
FRONTEND_PID=$!

# Wait a moment for servers to start
sleep 4

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}[BACKEND] Failed to start. Check for errors above.${NC}"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
else
    echo -e "${GREEN}[BACKEND] Server started successfully (PID: $BACKEND_PID)${NC}"
fi

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}[FRONTEND] Failed to start. Check for errors above.${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
else
    echo -e "${GREEN}[FRONTEND] Server started successfully (PID: $FRONTEND_PID)${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}[STATUS] Both servers are running${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend:  http://localhost:5001${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Wait for both processes and show their output
wait $BACKEND_PID $FRONTEND_PID
