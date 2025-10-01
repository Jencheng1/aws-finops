# FinOps Platform Context for Claude

## Project Overview
This is an AI-powered FinOps platform that provides cost optimization, budget prediction, and resource management for AWS environments.

## Active Services

### 1. FinOps Dashboard (Port 8502)
- **File**: `finops_intelligent_dashboard.py`
- **Direct URL**: http://localhost:8502
- **Nginx URL**: http://your-ec2-ip/ (port 80)
- **Features**: 
  - Real-time AWS cost visualization
  - AI budget predictions
  - Resource optimization recommendations
  - Human-in-the-loop feedback system
  - Cost anomaly detection
  - Full Analysis button (fixed and working)

### 2. Apptio Reconciliation Dashboard (Port 8504)
- **File**: `apptio_mcp_reconciliation.py`
- **Direct URL**: http://localhost:8504
- **Nginx URL**: http://your-ec2-ip/apptio (port 80)
- **Features**:
  - AWS expense to Apptio TBM mapping
  - Cost reconciliation
  - Service categorization

### 3. MCP Services
- **Cost Explorer MCP** (Port 8001): `aws_cost_explorer_mcp_server.py`
- **Apptio MCP** (Port 8002): `apptio_mcp_server.py`
- **Resource Intelligence MCP** (Port 8004): `aws_resource_intelligence_mcp_server.py`
- **Cloudability MCP** (Port 8005): `cloudability_mcp_server.py`

## Quick Start After Reboot

```bash
cd /home/ec2-user/finops/aws-finops
./start_finops_after_reboot.sh
```

## Python Version
- Using Python 3.7.16
- Note: No walrus operator (:=) support
- No streamlit.chat_input support (older streamlit version)

## Important Files
- `STARTUP_GUIDE.md` - Detailed startup instructions
- `start_finops_after_reboot.sh` - Quick start script
- `setup_systemd_services.sh` - Auto-start setup
- `finops_nginx.conf` - Nginx reverse proxy configuration

## AWS Services Used
- AWS Cost Explorer API
- EC2 API
- DynamoDB (for feedback storage)
- CloudWatch
- IAM

## Known Working Configuration
- FinOps Dashboard: `finops_intelligent_dashboard.py` on port 8502
- Apptio Reconciliation: `apptio_mcp_reconciliation.py` on port 8504
- Do NOT use `finops_dashboard.py` (has Python 3.8+ syntax)
- Do NOT use `enhanced_integrated_dashboard.py` (has Python 3.8+ syntax)
- Do NOT use `enhanced_dashboard_with_feedback.py` (not the correct version)

## Nginx Configuration
- Main dashboard accessible at http://your-ec2-ip/
- Apptio dashboard accessible at http://your-ec2-ip/apptio
- Configuration file: `/etc/nginx/conf.d/finops.conf`
- Nginx handles URL rewriting for Apptio path

## Recent Fixes
- Fixed Full Analysis button in finops_intelligent_dashboard.py
- Fixed Apptio nginx routing with URL rewriting
- Created backup: finops_intelligent_dashboard.py.backup

## Troubleshooting
- If services fail to start, check Python version compatibility
- Ensure AWS credentials are configured: `aws configure list`
- Check logs in the project directory (*.log files)
- Port 8501 may conflict with Docker, use 8502 instead
- For nginx issues: `sudo nginx -t` and `sudo tail -f /var/log/nginx/error.log`