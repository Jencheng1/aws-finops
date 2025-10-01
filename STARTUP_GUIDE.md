# FinOps Platform Startup Guide

This guide explains how to start all FinOps services after an EC2 reboot.

## Quick Start

Run this single command to start all services:

```bash
cd /home/ec2-user/finops/aws-finops
./start_finops_after_reboot.sh
```

## Manual Service Startup

If you prefer to start services individually:

### 1. Start FinOps Dashboard (Port 8502)
```bash
cd /home/ec2-user/finops/aws-finops
nohup python3 -m streamlit run finops_intelligent_dashboard.py --server.port 8502 --server.address 0.0.0.0 > dashboard_8502.log 2>&1 &
```

### 2. Start Apptio Reconciliation (Port 8504)
```bash
nohup python3 -m streamlit run apptio_mcp_reconciliation.py --server.port 8504 --server.address 0.0.0.0 > apptio_8504.log 2>&1 &
```

### 3. Start MCP Services
```bash
# Cost Explorer MCP (Port 8001)
nohup python3 aws_cost_explorer_mcp_server.py --port 8001 > mcp_cost_explorer.log 2>&1 &

# Apptio MCP (Port 8002)
nohup python3 apptio_mcp_server.py --port 8002 > mcp_apptio.log 2>&1 &

# Resource Intelligence MCP (Port 8004)
nohup python3 aws_resource_intelligence_mcp_server.py --port 8004 > mcp_resource.log 2>&1 &

# Cloudability MCP (Port 8005)
nohup python3 cloudability_mcp_server.py --port 8005 > mcp_cloudability.log 2>&1 &
```

## Service URLs

After starting, access the services at:

### Direct Access (if security groups allow):
- **FinOps Dashboard**: http://localhost:8502 or http://[EC2-PUBLIC-IP]:8502
- **Apptio Reconciliation**: http://localhost:8504 or http://[EC2-PUBLIC-IP]:8504
- **MCP Services**: Ports 8001, 8002, 8004, 8005 (API endpoints)

### Via Nginx (Port 80 - Recommended):
- **FinOps Dashboard**: http://[EC2-PUBLIC-IP]/
- **Apptio Reconciliation**: http://[EC2-PUBLIC-IP]/apptio

## Verify Services Are Running

Check all services status:
```bash
ps aux | grep -E "streamlit|mcp" | grep -v grep
```

Check service ports:
```bash
netstat -tulnp | grep -E "(8502|8504|8001|8002|8004|8005)"
```

## Stop All Services

To stop all services:
```bash
pkill -f "streamlit run"
pkill -f "mcp_server"
```

## Troubleshooting

### If services don't start:
1. Check Python version: `python3 --version` (should be 3.7+)
2. Check logs: `tail -f dashboard_8502.log`
3. Ensure AWS credentials are configured: `aws configure list`

### Port conflicts:
If ports are already in use, find the process:
```bash
sudo lsof -i :8502
```

## Auto-Start on Boot

To enable auto-start on EC2 reboot, run:
```bash
sudo ./setup_systemd_services.sh
```

This will create systemd services that start automatically on boot.

## Nginx Configuration (Recommended)

To set up Nginx reverse proxy for easy access via port 80:

```bash
# Copy the nginx configuration
sudo cp finops_nginx.conf /etc/nginx/conf.d/finops.conf

# Disable conflicting configs if any
sudo mv /etc/nginx/conf.d/finops-dashboard.conf /etc/nginx/conf.d/finops-dashboard.conf.disabled 2>/dev/null || true
sudo mv /etc/nginx/conf.d/streamlit.conf /etc/nginx/conf.d/streamlit.conf.disabled 2>/dev/null || true

# Test and reload nginx
sudo nginx -t && sudo systemctl reload nginx
```

## Important Notes

- The platform uses Python 3.7, which has some limitations (no walrus operator)
- AWS credentials must be configured for the services to work
- Security groups must allow inbound traffic on port 80 for Nginx access
- Direct access requires ports 8502 and 8504 to be open
- The correct working dashboard is `finops_intelligent_dashboard.py`
- Full Analysis button has been fixed and is working