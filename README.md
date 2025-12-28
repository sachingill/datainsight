# Text2SQL - E-commerce Analytics

Natural language to SQL query application built with Streamlit and LangChain.

## 🚀 Features

- **Natural Language to SQL**: Convert questions to SQL queries automatically
- **Interactive Visualizations**: Generate charts and graphs from query results
- **Query Tracing**: See how queries are generated and executed
- **Visitor Tracking**: Track unique visitors to the application
- **User API Keys**: Users provide their own OpenAI API keys for security

## 📋 Prerequisites

- Python 3.13+
- OpenAI API Key (provided by user in UI)
- SQLite database (`ecommerce.db`)

## 🛠️ Local Development

### Setup

```bash
# Clone repository
git clone <your-repo-url>
cd text2sql

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (if not exists)
python setup_database.py

# Run application
streamlit run src/app.py
```

## 🌐 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub and deploy
4. Main file path: `src/app.py`

See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md) for detailed instructions.

### Vultr/Other VPS

See [VULTR_DEPLOYMENT_GUIDE.md](VULTR_DEPLOYMENT_GUIDE.md) for server deployment.

## 📊 Database Schema

The application uses an e-commerce database with the following tables:

- **users**: Customer information and demographics
- **orders**: Order transactions
- **order_items**: Individual items in each order
- **products**: Product catalog
- **inventory_items**: Inventory tracking
- **events**: User interaction events
- **distribution_centers**: Warehouse locations

## 🔒 Security

- No hardcoded API keys
- Users provide their own OpenAI API keys
- API keys stored only in browser session
- Read-only database access recommended

## 📚 Documentation

- [App Flow](APP_FLOW.md) - Application architecture and flow
- [Query Tracing](QUERY_TRACING.md) - Query tracing feature
- [Streamlit Cloud Deployment](STREAMLIT_CLOUD_DEPLOYMENT.md) - Cloud deployment guide
- [Vultr Deployment](VULTR_DEPLOYMENT_GUIDE.md) - VPS deployment guide

## 🎯 Usage

1. Enter your OpenAI API key in the sidebar
2. Ask questions in natural language
3. View SQL queries and results
4. Generate visualizations by asking for charts/graphs

## 📝 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]

