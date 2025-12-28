# Vultr Deployment - Quick Start

## 🚀 Quick Deployment Steps

### 1. Create Vultr Server
- **Type**: Cloud Compute
- **OS**: Ubuntu 22.04 LTS
- **Size**: 2 vCPU, 4GB RAM (minimum) or 4 vCPU, 8GB RAM (recommended)
- **Location**: Choose closest to users
- **SSH Key**: Add your public key

### 2. Connect to Server
```bash
ssh root@YOUR_SERVER_IP
```

### 3. Run Setup Script
```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.13 python3.13-venv python3-pip git nginx supervisor

# Create app user
adduser --disabled-password --gecos "" text2sql
usermod -aG sudo text2sql
su - text2sql
```

### 4. Deploy Application
```bash
# Clone or upload your code
cd ~
git clone YOUR_REPO_URL text2sql
# OR upload via SCP from local machine

cd ~/text2sql

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

### 5. Configure Environment
```bash
# Create .env file
nano .env
```

Add:
```
OPENAI_API_KEY=your_actual_key_here
LLM_MODEL_NAME=gpt-4.1-2025-04-14
DATABASE=ecommerce
```

### 6. Setup Systemd Service
```bash
# Copy service file
sudo cp text2sql.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/text2sql.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable text2sql
sudo systemctl start text2sql
sudo systemctl status text2sql
```

### 7. Configure Nginx
```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/text2sql

# Edit server_name
sudo nano /etc/nginx/sites-available/text2sql

# Enable site
sudo ln -s /etc/nginx/sites-available/text2sql /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Setup SSL (Optional but Recommended)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 9. Configure Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 10. Test
Open browser: `http://YOUR_SERVER_IP` or `https://yourdomain.com`

---

## 📝 Important Files Created

- ✅ `VULTR_DEPLOYMENT_GUIDE.md` - Complete detailed guide
- ✅ `.env.example` - Environment variables template
- ✅ `deploy.sh` - Automated deployment script
- ✅ `nginx.conf` - Nginx configuration
- ✅ `text2sql.service` - Systemd service file
- ✅ `streamlit_config.toml` - Streamlit configuration
- ✅ `.gitignore` - Updated to exclude sensitive files
- ✅ `src/constants.py` - Updated to use environment variables

---

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains your API keys!
2. **Use environment variables** - Already configured in `constants.py`
3. **Restrict database access** - Update `llm_agent.py` to use `include_tables`
4. **Setup SSL** - Use Let's Encrypt for HTTPS
5. **Firewall** - Only open necessary ports

---

## 🆘 Quick Troubleshooting

```bash
# Check if app is running
sudo systemctl status text2sql

# View logs
sudo journalctl -u text2sql -f

# Restart app
sudo systemctl restart text2sql

# Check Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 📚 Next Steps

1. Read `VULTR_DEPLOYMENT_GUIDE.md` for detailed instructions
2. Setup monitoring and backups
3. Configure production optimizations
4. Add rate limiting and caching

---

**Your app should be live!** 🎉

