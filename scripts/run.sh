#!/bin/bash

# SwarmOS run script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_PID_FILE="$PROJECT_DIR/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/.frontend.pid"

case "$1" in
  start)
    echo "Starting SwarmOS infrastructure..."
    cd "$PROJECT_DIR"
    docker-compose up -d
    
    echo "Waiting for infrastructure to be ready..."
    sleep 3
    
    # Start backend
    if [ -f "$BACKEND_PID_FILE" ]; then
      OLD_PID=$(cat "$BACKEND_PID_FILE")
      if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Backend is already running (PID: $OLD_PID)"
      else
        rm "$BACKEND_PID_FILE"
      fi
    fi
    
    if [ ! -f "$BACKEND_PID_FILE" ]; then
      echo "Starting backend..."
      cd "$PROJECT_DIR"
      source venv/bin/activate
      uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/.backend.log" 2>&1 &
      BACKEND_PID=$!
      echo $BACKEND_PID > "$BACKEND_PID_FILE"
      echo "Backend started (PID: $BACKEND_PID)"
    fi
    
    # Start frontend
    if [ -f "$FRONTEND_PID_FILE" ]; then
      OLD_PID=$(cat "$FRONTEND_PID_FILE")
      if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Frontend is already running (PID: $OLD_PID)"
      else
        rm "$FRONTEND_PID_FILE"
      fi
    fi
    
    if [ ! -f "$FRONTEND_PID_FILE" ]; then
      echo "Starting frontend..."
      cd "$PROJECT_DIR/frontend"
      npm run dev > "$PROJECT_DIR/.frontend.log" 2>&1 &
      FRONTEND_PID=$!
      echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
      echo "Frontend started (PID: $FRONTEND_PID)"
    fi
    
    echo ""
    echo "SwarmOS is running!"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "To stop: ./scripts/run.sh stop"
    echo "To view logs: ./scripts/run.sh logs [backend|frontend]"
    ;;
    
  stop)
    echo "Stopping SwarmOS..."
    
    # Stop backend
    if [ -f "$BACKEND_PID_FILE" ]; then
      BACKEND_PID=$(cat "$BACKEND_PID_FILE")
      if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID"
        wait "$BACKEND_PID" 2>/dev/null
      fi
      rm "$BACKEND_PID_FILE"
    fi
    
    # Stop frontend
    if [ -f "$FRONTEND_PID_FILE" ]; then
      FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
      if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID"
        wait "$FRONTEND_PID" 2>/dev/null
      fi
      rm "$FRONTEND_PID_FILE"
    fi
    
    # Stop infrastructure
    echo "Stopping infrastructure..."
    cd "$PROJECT_DIR"
    docker-compose down
    
    echo "SwarmOS stopped."
    ;;
    
  logs)
    if [ -z "$2" ]; then
      echo "Backend logs:"
      echo "============="
      tail -f "$PROJECT_DIR/.backend.log" &
      BACKEND_TAIL_PID=$!
      echo ""
      echo "Frontend logs:"
      echo "============="
      tail -f "$PROJECT_DIR/.frontend.log" &
      FRONTEND_TAIL_PID=$!
      trap "kill $BACKEND_TAIL_PID $FRONTEND_TAIL_PID 2>/dev/null; exit" INT TERM
      wait
    elif [ "$2" == "backend" ]; then
      tail -f "$PROJECT_DIR/.backend.log"
    elif [ "$2" == "frontend" ]; then
      tail -f "$PROJECT_DIR/.frontend.log"
    else
      echo "Usage: $0 logs [backend|frontend]"
      exit 1
    fi
    ;;
    
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
    
  *)
    echo "Usage: $0 {start|stop|restart|logs [backend|frontend]}"
    exit 1
    ;;
esac
