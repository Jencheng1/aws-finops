#!/bin/bash

# Setup systemd services for FinOps Platform
# Run with sudo

echo "Setting up systemd services for FinOps Platform..."

# Create systemd service for FinOps Dashboard
cat > /tmp/finops-dashboard.service << EOF
[Unit]
Description=FinOps Dashboard Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/finops/aws-finops
ExecStart=/usr/bin/python3 -m streamlit run finops_intelligent_dashboard.py --server.port 8502 --server.address 0.0.0.0
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/ec2-user/finops/aws-finops/dashboard_8502.log
StandardError=append:/home/ec2-user/finops/aws-finops/dashboard_8502.log

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Apptio Reconciliation
cat > /tmp/apptio-reconciliation.service << EOF
[Unit]
Description=Apptio Reconciliation Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/finops/aws-finops
ExecStart=/usr/bin/python3 -m streamlit run apptio_mcp_reconciliation.py --server.port 8504 --server.address 0.0.0.0
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/ec2-user/finops/aws-finops/apptio_8504.log
StandardError=append:/home/ec2-user/finops/aws-finops/apptio_8504.log

[Install]
WantedBy=multi-user.target
EOF

# Copy services to systemd directory
sudo cp /tmp/finops-dashboard.service /etc/systemd/system/
sudo cp /tmp/apptio-reconciliation.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable finops-dashboard.service
sudo systemctl enable apptio-reconciliation.service

echo "✅ Systemd services created and enabled"
echo ""
echo "Services will start automatically on boot."
echo ""
echo "Manual control commands:"
echo "  Start:   sudo systemctl start finops-dashboard"
echo "  Stop:    sudo systemctl stop finops-dashboard"
echo "  Status:  sudo systemctl status finops-dashboard"
echo "  Logs:    sudo journalctl -u finops-dashboard -f"