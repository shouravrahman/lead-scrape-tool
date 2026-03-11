#!/bin/bash

# Lead Intelligence Platform - Development Setup & Run Script
# This script sets up and runs both backend and frontend with hot reload

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check environment files
check_env_files() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_warning ".env not found, copying from backend/.env.example"
        cp "$BACKEND_DIR/.env.example" "$PROJECT_DIR/.env"
        print_info "Please update .env with your API keys"
    fi
}

# Setup Backend
setup_backend() {
    print_header "Setting Up Backend (Python/FastAPI)"
    
    cd "$BACKEND_DIR"
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    source venv/bin/activate
    print_info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    print_success "Backend dependencies installed"
    
    cd "$PROJECT_DIR"
}

# Setup Frontend
setup_frontend() {
    print_header "Setting Up Frontend (Vue 3 + Vite)"
    
    cd "$FRONTEND_DIR"
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing Node dependencies..."
        npm install --silent
        print_success "Frontend dependencies installed"
    else
        print_info "node_modules already exist, skipping npm install"
    fi
    
    cd "$PROJECT_DIR"
}

# Start services
start_services() {
    print_header "Starting Development Services"
    
    # Start Backend
    print_info "Starting Backend (http://localhost:8000)..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    print_success "Backend started (PID: $BACKEND_PID)"
    
    sleep 2
    
    # Start Frontend
    print_info "Starting Frontend with Vite (http://localhost:5173)..."
    cd "$FRONTEND_DIR"
    npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    print_success "Frontend started (PID: $FRONTEND_PID)"
    
    echo ""
    print_header "🎉 Development Environment Ready!"
    echo ""
    echo "Services:"
    echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo "Process IDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
    echo ""
    print_info "Press Ctrl+C to stop services"
    echo ""
    
    # Handle signals
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
}

# Commands
case "${1:-start}" in
    install|setup)
        check_env_files
        setup_backend
        setup_frontend
        print_header "✓ Setup Complete!"
        print_success "Run: ./dev.sh start"
        ;;
    start|run)
        if [ ! -d "$BACKEND_DIR/venv" ] || [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            print_info "First run detected, installing dependencies..."
            ./dev.sh install
        fi
        start_services
        ;;
    backend)
        if [ ! -d "$BACKEND_DIR/venv" ]; then
            setup_backend
        fi
        cd "$BACKEND_DIR"
        source venv/bin/activate
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ;;
    frontend)
        if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            setup_frontend
        fi
        cd "$FRONTEND_DIR"
        npm run dev
        ;;
    build)
        print_header "Building Frontend for Production"
        cd "$FRONTEND_DIR"
        npm run build
        print_success "Build complete! Output in: frontend/dist/"
        ;;
    *)
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  install, setup - Install all dependencies"
        echo "  start, run     - Install deps and start both services (default)"
        echo "  backend        - Start backend server only"
        echo "  frontend       - Start frontend dev server only"
        echo "  build          - Build frontend for production"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh install    # Install dependencies first time"
        echo "  ./dev.sh start      # Start dev server"
        echo "  ./dev.sh            # Same as ./dev.sh start"
        ;;
esac
