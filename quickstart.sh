#!/bin/bash

# AI-Powered FinOps System - Quick Start Script
# This script automates the deployment and startup of the complete system

set -e

echo "======================================"
echo "AI-Powered FinOps System Quick Start"
echo "======================================"
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
print_status "Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi
print_status "pip3 found"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install AWS CLI."
    exit 1
fi
print_status "AWS CLI found: $(aws --version | cut -d' ' -f1)"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure'."
    exit 1
fi
print_status "AWS credentials configured"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS Account ID: $ACCOUNT_ID"

echo
echo "======================================"
echo "Step 1: Setting up Python environment"
echo "======================================"

# Create virtual environment if it doesn't exist
if [ ! -d "finops-env" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv finops-env
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source finops-env/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet boto3 streamlit pandas plotly websocket-client pytest

echo
echo "======================================"
echo "Step 2: Deploying AWS Resources"
echo "======================================"

# Check if deployment already exists
if [ -f "finops_config.json" ]; then
    print_warning "Existing deployment found. Checking status..."
    
    # Check Lambda function
    if aws lambda get-function --function-name finops-cost-analysis &> /dev/null; then
        print_status "Lambda function exists"
        
        read -p "Do you want to redeploy AWS resources? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Skipping AWS deployment"
        else
            print_status "Redeploying AWS resources..."
            python3 deploy_finops_system.py
        fi
    else
        print_status "Lambda function not found. Deploying..."
        python3 deploy_finops_system.py
    fi
else
    print_status "No existing deployment found. Deploying AWS resources..."
    python3 deploy_finops_system.py
fi

echo
echo "======================================"
echo "Step 3: Starting Services"
echo "======================================"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start MCP server in background
print_status "Starting MCP server..."
if check_port 8765; then
    print_warning "MCP server already running on port 8765"
else
    nohup python3 mcp_appitio_integration.py > mcp_server.log 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > mcp_server.pid
    sleep 2
    
    if check_port 8765; then
        print_status "MCP server started (PID: $MCP_PID)"
    else
        print_warning "MCP server failed to start. Check mcp_server.log for details."
    fi
fi

echo
echo "======================================"
echo "Step 4: Running Tests"
echo "======================================"

print_status "Running system tests..."
python3 test_chatbot_integration.py || print_warning "Some tests failed. Check output above."

echo
echo "======================================"
echo "Step 5: Starting Dashboard"
echo "======================================"

# Check if Streamlit is already running
if check_port 8501; then
    print_warning "Streamlit already running on port 8501"
    print_status "Dashboard URL: http://localhost:8501"
else
    print_status "Starting Streamlit dashboard..."
    print_status "Dashboard URL: http://localhost:8501"
    echo
    echo "Press Ctrl+C to stop the dashboard"
    echo
    streamlit run finops_dashboard_with_chatbot.py
fi

# Cleanup function
cleanup() {
    echo
    print_status "Shutting down services..."
    
    # Stop MCP server if we started it
    if [ -f "mcp_server.pid" ]; then
        MCP_PID=$(cat mcp_server.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            kill $MCP_PID
            print_status "MCP server stopped"
        fi
        rm mcp_server.pid
    fi
    
    deactivate 2>/dev/null || true
    print_status "Cleanup complete"
}

# Set up cleanup on exit
trap cleanup EXIT