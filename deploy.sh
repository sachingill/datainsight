#!/bin/bash
# Deployment script for Vultr server
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.13 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install/update dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${RED}Please edit .env file with your configuration!${NC}"
    fi
fi

# Check if database exists
if [ ! -f "ecommerce.db" ]; then
    echo -e "${YELLOW}Database not found. Running setup...${NC}"
    if [ -f "setup_database.py" ]; then
        python setup_database.py
    else
        echo -e "${RED}Warning: setup_database.py not found. Please create database manually.${NC}"
    fi
fi

# Restart service if systemd service exists
if systemctl is-active --quiet text2sql 2>/dev/null; then
    echo -e "${GREEN}Restarting text2sql service...${NC}"
    sudo systemctl restart text2sql
    echo -e "${GREEN}Service restarted!${NC}"
else
    echo -e "${YELLOW}Systemd service not found. Skipping service restart.${NC}"
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"

