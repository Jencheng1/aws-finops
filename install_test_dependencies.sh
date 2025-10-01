#!/bin/bash
# Install dependencies for UI testing

echo "Installing test dependencies..."

# Install Chrome
if ! command -v google-chrome &> /dev/null; then
    echo "Installing Google Chrome..."
    cd /tmp
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    sudo yum install -y google-chrome-stable_current_x86_64.rpm
    rm google-chrome-stable_current_x86_64.rpm
else
    echo "✓ Chrome already installed"
fi

# Install ChromeDriver
if ! command -v chromedriver &> /dev/null; then
    echo "Installing ChromeDriver..."
    cd /tmp
    # Get latest ChromeDriver version
    CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
    echo "Chrome version: $CHROME_VERSION"
    
    # Download ChromeDriver
    wget -N https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip -P /tmp/
    unzip -o /tmp/chromedriver-linux64.zip -d /tmp/
    sudo mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    rm -rf /tmp/chromedriver*
else
    echo "✓ ChromeDriver already installed"
fi

# Install Python packages
echo "Installing Python packages..."
pip3 install selenium --user
pip3 install webdriver-manager --user

echo "✓ All dependencies installed"
chromedriver --version