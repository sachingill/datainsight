# Streamlit Cloud Deployment Guide

## ✅ Yes, You Can Deploy to Streamlit Cloud!

Streamlit Cloud (Community or Team) supports deploying your application with SQLite database. Here's everything you need to know.

---

## 🚀 Deployment Options

### 1. **Streamlit Community Cloud** (Free)
- ✅ Free hosting
- ✅ Automatic deployments from GitHub
- ✅ Supports SQLite databases
- ⚠️ Ephemeral file system (files reset on restart)
- ⚠️ Limited resources

### 2. **Streamlit Team Cloud** (Paid)
- ✅ Persistent storage
- ✅ More resources
- ✅ Better for production

---

## 📋 Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Streamlit Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Database File** - Your SQLite database needs to be in the repository

---

## 📦 Files Needed for Deployment

### Required Files

1. **`requirements.txt`** ✅ (Already exists)
2. **`.streamlit/config.toml`** (Optional - for configuration)
3. **`README.md`** (Optional - but recommended)
4. **Database file** (`ecommerce.db`) - Must be in repository

### File Structure

```
text2sql/
├── requirements.txt          ✅ Required
├── README.md                 📝 Recommended
├── .streamlit/
│   └── config.toml          ⚙️ Optional
├── src/
│   ├── app.py               ✅ Main app
│   ├── constants.py         ✅ Config
│   ├── llm_agent.py         ✅ Agents
│   ├── helper.py            ✅ Helpers
│   ├── trace_handler.py     ✅ Tracing
│   └── visitor_tracker.py   ✅ Visitor tracking
├── data/                     📁 CSV files (if needed)
├── ecommerce.db             ✅ SQLite database
└── setup_database.py         🔧 Database setup (optional)
```

---

## 🔧 Setup Steps

### Step 1: Prepare Your Repository

```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Create `.streamlit/config.toml` (Optional)

Create this file for better configuration:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### Step 3: Ensure Database is in Repository

**Important**: SQLite database must be committed to Git:

```bash
# Add database to repository
git add ecommerce.db
git commit -m "Add database file"
git push origin main
```

**Note**: For large databases (>100MB), consider:
- Using Git LFS (Large File Storage)
- Or initializing database on first run (see below)

### Step 4: Update `.gitignore` (if needed)

Make sure you're not ignoring the database:

```gitignore
# Don't ignore the database file
# ecommerce.db  <- Remove this if present
```

---

## ⚠️ Important Considerations

### 1. **Ephemeral File System (Community Cloud)**

**Problem**: Streamlit Community Cloud has an ephemeral file system. Files can be reset.

**Solutions**:

#### Option A: Commit Database to Git
- ✅ Database persists across deployments
- ✅ Simple and works well
- ⚠️ Database size limit (~100MB for Git)
- ⚠️ Database changes are versioned

#### Option B: Initialize Database on First Run
- ✅ Always fresh database
- ✅ No Git size issues
- ⚠️ Database resets on restart
- ⚠️ Slower first load

#### Option C: Use External Storage (Recommended for Production)
- ✅ Persistent storage
- ✅ No size limits
- ⚠️ Requires additional setup (S3, etc.)

### 2. **Database Initialization Script**

If you want to initialize database on first run:

```python
# Add to app.py at the top
import os
from pathlib import Path

DB_PATH = Path("ecommerce.db")
if not DB_PATH.exists():
    # Run setup script
    from setup_database import setup_database
    setup_database()
```

### 3. **Environment Variables**

For API keys and secrets, use Streamlit Secrets:

1. Go to your app settings in Streamlit Cloud
2. Click "Secrets"
3. Add your secrets:

```toml
# .streamlit/secrets.toml (managed in Streamlit Cloud UI)
OPENAI_API_KEY = "your-key-here"  # Optional - users can still provide in UI
```

---

## 🚀 Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for Streamlit Cloud"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `your-username/text2sql`
5. Select branch: `main`
6. Main file path: `src/app.py`
7. Click "Deploy"

### 3. Configure Secrets (Optional)

1. Go to app settings
2. Click "Secrets"
3. Add any environment variables needed

---

## 📝 Updated Files for Deployment

### 1. Create `.streamlit/config.toml`

```bash
mkdir -p .streamlit
```

Then create `.streamlit/config.toml`:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
port = 8501

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### 2. Update `requirements.txt` (if needed)

Make sure all dependencies are listed:

```txt
streamlit==1.50.0
langchain-experimental==0.3.4
langchain-openai==0.3.33
langchain-community
networkx>=3.0
plotly==6.3.0
matplotlib==3.10.6
python-dotenv>=1.0.0
# ... (your existing requirements)
```

### 3. Create `README.md` (Recommended)

```markdown
# Text2SQL - E-commerce Analytics

Natural language to SQL query application with Streamlit.

## Features

- Natural language to SQL conversion
- Interactive data visualization
- Query tracing and debugging
- Visitor tracking

## Deployment

Deployed on Streamlit Cloud: [your-app-url]

## Local Development

```bash
pip install -r requirements.txt
streamlit run src/app.py
```
```

---

## 🔒 Security Considerations

### 1. **API Keys**
- ✅ Users provide their own API keys (current implementation)
- ✅ No hardcoded keys in code
- ✅ Optional: Use Streamlit Secrets for default key

### 2. **Database Access**
- ✅ Read-only access recommended
- ✅ SQLite is file-based (no network exposure)
- ✅ Consider adding query limits

### 3. **Visitor Tracking**
- ✅ File-based tracking (visitor_log.json)
- ⚠️ Resets on Community Cloud restart
- ✅ Consider external storage for production

---

## 🎯 Best Practices

### 1. **Database Size**
- Keep database under 100MB for Git
- Use compression if needed
- Consider splitting into multiple files

### 2. **Performance**
- Index your database tables
- Optimize queries
- Use connection pooling (if needed)

### 3. **Error Handling**
- Add try-catch blocks
- Show user-friendly error messages
- Log errors appropriately

### 4. **Monitoring**
- Use Streamlit Cloud logs
- Monitor visitor counts
- Track query performance

---

## 🐛 Troubleshooting

### Database Not Found

**Error**: `FileNotFoundError: ecommerce.db`

**Solution**:
1. Ensure database is committed to Git
2. Check file path in `constants.py`
3. Use absolute paths if needed

### Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
1. Check `requirements.txt` has all dependencies
2. Ensure Python version compatibility
3. Check import paths in code

### Memory Issues

**Error**: Out of memory

**Solution**:
1. Optimize database queries
2. Add LIMIT clauses
3. Consider pagination

---

## 📊 Deployment Checklist

- [ ] All code pushed to GitHub
- [ ] `requirements.txt` is complete
- [ ] Database file is in repository (or setup script ready)
- [ ] `.streamlit/config.toml` created (optional)
- [ ] `README.md` created (recommended)
- [ ] No hardcoded secrets
- [ ] Tested locally
- [ ] App deployed on Streamlit Cloud
- [ ] Secrets configured (if needed)
- [ ] App tested on cloud

---

## 🚀 Quick Start Deployment

```bash
# 1. Ensure database exists
ls ecommerce.db  # Should exist

# 2. Create config file
mkdir -p .streamlit
# Create .streamlit/config.toml (see above)

# 3. Commit everything
git add .
git commit -m "Ready for Streamlit Cloud"
git push origin main

# 4. Deploy on Streamlit Cloud
# Go to share.streamlit.io and follow steps
```

---

## 💡 Alternative: Database Initialization

If you don't want to commit the database, initialize it on first run:

```python
# Add to src/app.py at the top
import os
from pathlib import Path
from constants import DATABASE

# Check if database exists, if not, create it
if not Path(DATABASE).exists():
    try:
        from setup_database import setup_database
        st.info("🔄 Initializing database... This may take a moment.")
        setup_database()
        st.success("✅ Database initialized!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error initializing database: {e}")
```

---

## 📚 Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

---

## ✅ Summary

**Yes, you can deploy to Streamlit Cloud with SQLite!**

**Key Points**:
- ✅ SQLite works on Streamlit Cloud
- ✅ Commit database to Git (or initialize on first run)
- ✅ All your current code will work
- ✅ Users provide their own API keys (secure)
- ⚠️ Database may reset on Community Cloud (ephemeral)
- ✅ Consider Team Cloud for persistent storage

**Your application is ready for deployment!** 🎉

