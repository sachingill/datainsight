# Vultr Deployment Guide for Text2SQL Application

## 🚀 Overview

This guide will help you deploy your Text2SQL Streamlit application to Vultr cloud infrastructure.

---

## 📋 Prerequisites

1. **Vultr Account** - Sign up at [vultr.com](https://www.vultr.com)
2. **SSH Access** - Your local machine's SSH key
3. **Domain (Optional)** - For custom domain setup
4. **Git Repository** - Your code in a Git repo (GitHub/GitLab)

---

## 🏗️ Deployment Architecture

```
┌─────────────────────────────────────┐
│  Vultr Cloud Server                 │
│  ┌───────────────────────────────┐ │
│  │  Ubuntu 22.04 LTS              │ │
│  │  ┌───────────────────────────┐ │ │
│  │  │  Nginx (Reverse Proxy)     │ │ │
│  │  │  Port: 80, 443            │ │ │
│  │  └───────────┬───────────────┘ │ │
│  │              │                  │ │
│  │  ┌───────────▼───────────────┐ │ │
│  │  │  Streamlit App            │ │ │
│  │  │  Port: 8501               │ │ │
│  │  │  └─ Python 3.13           │ │ │
│  │  │  └─ Virtual Environment   │ │ │
│  │  └───────────────────────────┘ │ │
│  │                                │ │
│  │  ┌───────────────────────────┐ │ │
│  │  │  SQLite Database          │ │ │
│  │  │  └─ ecommerce.db         │ │ │
│  │  └───────────────────────────┘ │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 📦 Step 1: Create Vultr Instance

### 1.1 Create Server

1. Log into Vultr Dashboard
2. Click **"Deploy Server"**
3. Choose:
   - **Server Type**: Cloud Compute
   - **CPU & Storage**: 
     - Minimum: 2 vCPU, 4GB RAM (for testing)
     - Recommended: 4 vCPU, 8GB RAM (for production)
   - **Server Location**: Choose closest to your users
   - **OS**: Ubuntu 22.04 LTS
   - **SSH Keys**: Add your SSH public key
4. Click **"Deploy Now"**

### 1.2 Note Server Details

- **IP Address**: `YOUR_SERVER_IP`
- **Root Password**: (if not using SSH keys)
- **Username**: `root` (or your configured user)

---

## 🔧 Step 2: Initial Server Setup

### 2.1 Connect to Server

```bash
ssh root@YOUR_SERVER_IP
# or
ssh your_user@YOUR_SERVER_IP
```

### 2.2 Update System

```bash
apt update && apt upgrade -y
```

### 2.3 Install Required Packages

```bash
# Install Python 3.13 and dependencies
apt install -y python3.13 python3.13-venv python3-pip git nginx supervisor

# Install build dependencies
apt install -y build-essential python3.13-dev
```

### 2.4 Create Application User

```bash
# Create dedicated user for app
adduser --disabled-password --gecos "" text2sql
usermod -aG sudo text2sql

# Switch to app user
su - text2sql
```

---

## 📥 Step 3: Deploy Application

### 3.1 Clone Repository

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone https://github.com/YOUR_USERNAME/text2sql.git
# OR upload via SCP:
# scp -r /local/path/text2sql user@YOUR_SERVER_IP:~/apps/
```

### 3.2 Setup Virtual Environment

```bash
cd ~/apps/text2sql

# Create virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3.3 Setup Database

```bash
# Make sure database file exists
# If you have setup_database.py:
python setup_database.py

# OR copy database file from local:
# scp ecommerce.db user@YOUR_SERVER_IP:~/apps/text2sql/
```

### 3.4 Configure Environment Variables

```bash
# Create .env file (DO NOT commit this!)
nano .env
```

Add:
```bash
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL_NAME=gpt-4.1-2025-04-14
DATABASE=ecommerce
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=127.0.0.1
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

**Security**: Make sure `.env` is in `.gitignore`!

---

## 🔒 Step 4: Security Configuration

### 4.1 Update Constants to Use Environment Variables

The application should read from environment variables instead of hardcoded values.

### 4.2 Setup Firewall

```bash
# Install and configure UFW
apt install -y ufw

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
ufw status
```

### 4.3 Setup SSL Certificate (Let's Encrypt)

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## ⚙️ Step 5: Configure Streamlit

### 5.1 Create Streamlit Config

```bash
mkdir -p ~/.streamlit
nano ~/.streamlit/config.toml
```

Add:
```toml
[server]
port = 8501
address = "127.0.0.1"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### 5.2 Create Systemd Service

```bash
sudo nano /etc/systemd/system/text2sql.service
```

Add:
```ini
[Unit]
Description=Text2SQL Streamlit Application
After=network.target

[Service]
Type=simple
User=text2sql
WorkingDirectory=/home/text2sql/apps/text2sql
Environment="PATH=/home/text2sql/apps/text2sql/venv/bin"
ExecStart=/home/text2sql/apps/text2sql/venv/bin/streamlit run src/app.py --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable text2sql
sudo systemctl start text2sql
sudo systemctl status text2sql
```

---

## 🌐 Step 6: Configure Nginx

### 6.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/text2sql
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS (after SSL setup)
    # return 301 https://$server_name$request_uri;

    # For initial setup, use HTTP:
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### 6.2 Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/text2sql /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

## 🔄 Step 7: Setup Auto-Deployment (Optional)

### 7.1 Create Deployment Script

```bash
nano ~/deploy.sh
```

Add:
```bash
#!/bin/bash
cd ~/apps/text2sql
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart text2sql
echo "Deployment complete!"
```

Make executable:
```bash
chmod +x ~/deploy.sh
```

### 7.2 Setup GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` in your repo.

---

## 📊 Step 8: Monitoring & Logs

### 8.1 View Application Logs

```bash
# Streamlit logs
sudo journalctl -u text2sql -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 8.2 Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/text2sql
```

Add:
```
/home/text2sql/apps/text2sql/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## 🧪 Step 9: Testing

### 9.1 Test Locally on Server

```bash
# SSH into server
ssh user@YOUR_SERVER_IP

# Test Streamlit
cd ~/apps/text2sql
source venv/bin/activate
streamlit run src/app.py --server.port=8501
```

### 9.2 Test from Browser

1. Open `http://YOUR_SERVER_IP` (or your domain)
2. Verify application loads
3. Test a query
4. Check logs for errors

---

## 🔧 Step 10: Production Optimizations

### 10.1 Database Security

```python
# Update src/llm_agent.py to use include_tables
db = SQLDatabase.from_uri(
    f"sqlite:///{DATABASE}",
    include_tables=["orders", "products", "users", "order_items"],  # Whitelist
    sample_rows_in_table_info=3
)
```

### 10.2 Add Rate Limiting

Install:
```bash
pip install streamlit-rate-limiter
```

### 10.3 Add Caching

```python
# Add to src/app.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_query(query_hash: str):
    # Cache implementation
    pass
```

### 10.4 Setup Backup

```bash
# Create backup script
nano ~/backup.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/apps/text2sql/ecommerce.db ~/backups/ecommerce_$DATE.db
# Keep only last 7 days
find ~/backups -name "ecommerce_*.db" -mtime +7 -delete
```

Setup cron:
```bash
crontab -e
# Add: 0 2 * * * /home/text2sql/backup.sh
```

---

## 🚨 Troubleshooting

### Application Not Starting

```bash
# Check service status
sudo systemctl status text2sql

# Check logs
sudo journalctl -u text2sql -n 50

# Check if port is in use
sudo netstat -tulpn | grep 8501
```

### Nginx 502 Bad Gateway

```bash
# Check if Streamlit is running
sudo systemctl status text2sql

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Test Streamlit directly
curl http://127.0.0.1:8501
```

### Database Issues

```bash
# Check database file permissions
ls -la ecommerce.db

# Fix permissions if needed
chmod 644 ecommerce.db
chown text2sql:text2sql ecommerce.db
```

### Memory Issues

```bash
# Check memory usage
free -h

# Check if swap is enabled
swapon --show

# Add swap if needed (2GB example)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📈 Performance Tuning

### 1. Increase Nginx Timeout

```nginx
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
```

### 2. Enable Gzip Compression

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### 3. Add Caching Headers

```nginx
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔐 Security Checklist

- [ ] Environment variables in `.env` (not hardcoded)
- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Database access restricted (include_tables)
- [ ] Rate limiting enabled
- [ ] Regular backups configured
- [ ] Logs monitored
- [ ] Updates automated
- [ ] SSH key-only access (disable password auth)
- [ ] Non-root user for application

---

## 📝 Quick Reference Commands

```bash
# Start application
sudo systemctl start text2sql

# Stop application
sudo systemctl stop text2sql

# Restart application
sudo systemctl restart text2sql

# View logs
sudo journalctl -u text2sql -f

# Update application
cd ~/apps/text2sql && git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart text2sql

# Check status
sudo systemctl status text2sql
sudo systemctl status nginx
```

---

## 🎯 Next Steps

1. **Monitor Performance**: Set up monitoring (e.g., Prometheus, Grafana)
2. **Add CI/CD**: Automate deployments
3. **Scale Horizontally**: Add load balancer for multiple instances
4. **Database Migration**: Consider PostgreSQL for production
5. **Add Authentication**: Implement user authentication
6. **API Rate Limiting**: Add API rate limits per user

---

## 📚 Additional Resources

- [Vultr Documentation](https://www.vultr.com/docs/)
- [Streamlit Deployment](https://docs.streamlit.io/deploy)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)

---

## ✅ Deployment Checklist

- [ ] Vultr instance created
- [ ] Server updated and secured
- [ ] Application cloned and configured
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database setup
- [ ] Environment variables configured
- [ ] Streamlit service created
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Application tested
- [ ] Monitoring setup
- [ ] Backups configured

---

**Your application should now be live at `http://YOUR_SERVER_IP` or `https://yourdomain.com`!** 🎉

