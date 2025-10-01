#!/bin/bash

# FinOps Platform Startup Script
# Use this after EC2 reboot to start all services

echo "=================================="
echo "Starting FinOps Platform Services"
echo "=================================="
echo "Time: $(date)"
echo ""

# Change to project directory
cd /home/ec2-user/finops/aws-finops || exit 1

# Function to check if port is in use
check_port() {
    if netstat -tulnp 2>/dev/null | grep -q ":$1 "; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f "streamlit run" 2>/dev/null || true
pkill -f "mcp_server" 2>/dev/null || true
sleep 2

# Start FinOps Dashboard
echo ""
echo "1. Starting FinOps Dashboard (Port 8502)..."
if check_port 8502; then
    nohup python3 -m streamlit run finops_intelligent_dashboard.py \
        --server.port 8502 \
        --server.address 0.0.0.0 \
        > dashboard_8502.log 2>&1 &
    echo "✅ FinOps Dashboard started"
else
    echo "❌ Could not start FinOps Dashboard - port 8502 is in use"
fi

# Start Apptio Reconciliation
echo ""
echo "2. Starting Apptio Reconciliation (Port 8504)..."
if check_port 8504; then
    nohup python3 -m streamlit run apptio_mcp_reconciliation.py \
        --server.port 8504 \
        --server.address 0.0.0.0 \
        > apptio_8504.log 2>&1 &
    echo "✅ Apptio Reconciliation started"
else
    echo "❌ Could not start Apptio Reconciliation - port 8504 is in use"
fi

# Start MCP Services
echo ""
echo "3. Starting MCP Services..."

# Cost Explorer MCP
if check_port 8001; then
    nohup python3 aws_cost_explorer_mcp_server.py --port 8001 \
        > mcp_cost_explorer.log 2>&1 &
    echo "✅ Cost Explorer MCP started (Port 8001)"
fi

# Apptio MCP
if check_port 8002; then
    nohup python3 apptio_mcp_server.py --port 8002 \
        > mcp_apptio.log 2>&1 &
    echo "✅ Apptio MCP started (Port 8002)"
fi

# Resource Intelligence MCP
if check_port 8004; then
    nohup python3 aws_resource_intelligence_mcp_server.py --port 8004 \
        > mcp_resource.log 2>&1 &
    echo "✅ Resource Intelligence MCP started (Port 8004)"
fi

# Cloudability MCP
if check_port 8005; then
    nohup python3 cloudability_mcp_server.py --port 8005 \
        > mcp_cloudability.log 2>&1 &
    echo "✅ Cloudability MCP started (Port 8005)"
fi

# Wait for services to start
echo ""
echo "Waiting for services to initialize..."
sleep 5

# Verify services
echo ""
echo "=================================="
echo "Service Status:"
echo "=================================="
ps aux | grep -E "streamlit|mcp" | grep -v grep | awk '{print "✅", $11, $12, $13}'

echo ""
echo "=================================="
echo "Access URLs:"
echo "=================================="
# Get EC2 public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "Via Nginx (Port 80):"
echo "FinOps Dashboard:        http://$PUBLIC_IP/"
echo "Apptio Reconciliation:   http://$PUBLIC_IP/apptio"
echo ""
echo "Direct Access:"
echo "FinOps Dashboard:        http://$PUBLIC_IP:8502"
echo "Apptio Reconciliation:   http://$PUBLIC_IP:8504"
echo ""
echo "Local Access:"
echo "FinOps Dashboard:        http://localhost:8502"
echo "Apptio Reconciliation:   http://localhost:8504"
echo ""
echo "All services started successfully!"
echo "==================================""""