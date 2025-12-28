# User API Key Feature

## 🎯 Overview

The application now allows users to enter their own OpenAI API key instead of using a hardcoded key. This provides better security and allows users to use their own API credits.

---

## ✨ Features

### 1. **Sidebar API Key Input**
- Secure password-type input field
- Real-time validation
- Visual feedback (success/warning messages)
- Masked display of saved key

### 2. **Session-Based Storage**
- API key stored only in browser session state
- Never logged or saved to disk
- Cleared when browser session ends
- Secure and private

### 3. **Automatic Agent Reinitialization**
- Agents automatically reinitialize when API key changes
- No page refresh needed
- Seamless user experience

### 4. **Validation**
- Format validation (must start with "sk-")
- Length validation (minimum 20 characters)
- Clear error messages

---

## 🔧 Implementation Details

### Changes Made

#### 1. **`src/llm_agent.py`**
- Updated all agent initialization functions to accept `api_key` parameter:
  - `get_chat_openai(model_name, api_key=None)`
  - `get_sql_toolkit(tool_llm_name, api_key=None)`
  - `get_agent_llm(agent_llm_name, api_key=None)`
  - `initialize_sql_agent(..., api_key=None)`
  - `initialize_python_agent(..., api_key=None)`

#### 2. **`src/app.py`**
- Added sidebar with API key input
- Added validation function `is_valid_api_key()`
- Updated session state management
- Added API key change detection
- Added agent initialization checks
- Added helpful instructions and tips

#### 3. **`src/constants.py`**
- Already updated to use environment variables
- Falls back to default if no user key provided

---

## 🎨 User Interface

### Sidebar Components

1. **API Key Input Field**
   - Password type (masked)
   - Placeholder: "sk-..."
   - Help text explaining security

2. **Status Indicators**
   - ✅ Success: Valid key saved
   - ⚠️ Warning: Invalid key format
   - ℹ️ Info: Using saved key

3. **Key Preview**
   - Shows first 7 and last 4 characters
   - Format: `sk-xxxx...xxxx`
   - Helps verify correct key

4. **Help Section**
   - Expandable instructions
   - Link to OpenAI platform
   - Step-by-step guide

---

## 🔒 Security Features

### 1. **No Persistent Storage**
- API key never saved to disk
- Only stored in browser session
- Cleared on browser close

### 2. **No Logging**
- API key never logged
- Not included in error messages
- Not sent to any external services

### 3. **Password Input**
- Masked input field
- Prevents shoulder surfing
- Standard security practice

### 4. **Validation**
- Format checking prevents common mistakes
- Length validation prevents invalid keys
- Clear error messages guide users

---

## 📋 Usage Flow

### First Time User

1. User opens application
2. Sees warning: "Please configure your OpenAI API key"
3. Opens sidebar
4. Enters API key
5. System validates key
6. Agents initialize with user's key
7. User can now use the application

### Returning User (Same Session)

1. User opens application
2. Previously saved key is used automatically
3. No need to re-enter
4. Can change key if needed

### Key Change

1. User enters new key in sidebar
2. System detects change
3. Agents reinitialize automatically
4. Old key is replaced
5. No data loss

---

## 🛠️ Technical Details

### API Key Flow

```
User Input
    ↓
Validation (format, length)
    ↓
Store in session_state
    ↓
Set environment variable
    ↓
Reinitialize agents
    ↓
Ready to use
```

### Agent Initialization

```python
# Check for user API key
user_api_key = st.session_state.get('openai_api_key', default_key)

# Initialize agents with user key
if user_api_key:
    sql_agent = initialize_sql_agent(api_key=user_api_key)
    python_agent = initialize_python_agent(api_key=user_api_key)
```

### Validation Logic

```python
def is_valid_api_key(key):
    if not key:
        return False, "Please enter an API key"
    if not key.startswith("sk-"):
        return False, "API key should start with 'sk-'"
    if len(key) < 20:
        return False, "API key seems too short"
    return True, "Valid API key format"
```

---

## 🚀 Benefits

### For Users
- ✅ Use their own API credits
- ✅ Better privacy (key not stored on server)
- ✅ Control over API usage
- ✅ No need to trust server with key

### For Deployment
- ✅ No hardcoded API keys in code
- ✅ No need to manage API keys on server
- ✅ Reduced security risk
- ✅ Lower operational costs

### For Development
- ✅ Easy testing with different keys
- ✅ No need to share keys
- ✅ Better security practices

---

## 📝 Configuration

### Default Behavior

If no user API key is provided:
- Falls back to `OPENAI_API_KEY` from environment variables
- Or uses default from `constants.py` (if set)
- Shows warning if no key available

### Environment Variables

Still supported for:
- Development/testing
- Server-side fallback
- Default configuration

---

## 🔍 Error Handling

### Invalid Key Format
- Shows warning message
- Prevents agent initialization
- Clear instructions on how to fix

### Missing Key
- Shows warning in main area
- Prevents query submission
- Instructions in sidebar

### Key Change During Session
- Automatically reinitializes agents
- No data loss
- Seamless transition

---

## 🎯 Best Practices

### For Users
1. **Get API Key**: Visit [OpenAI Platform](https://platform.openai.com/)
2. **Keep It Secret**: Never share your API key
3. **Monitor Usage**: Check usage on OpenAI dashboard
4. **Rotate Keys**: Change key if compromised

### For Developers
1. **Never Log Keys**: Don't log API keys in code
2. **Validate Input**: Always validate user input
3. **Clear Messages**: Provide clear error messages
4. **Security First**: Follow security best practices

---

## 🐛 Troubleshooting

### "Please configure your OpenAI API key"
- **Solution**: Enter API key in sidebar
- **Check**: Key format (should start with "sk-")

### "Agents not initialized"
- **Solution**: Check API key is valid
- **Check**: Refresh page and re-enter key

### "API key seems too short"
- **Solution**: Check you copied the full key
- **Check**: No extra spaces or characters

### Key not working
- **Solution**: Verify key on OpenAI platform
- **Solution**: Check key has sufficient credits
- **Solution**: Try generating a new key

---

## 📚 Related Files

- `src/app.py` - Main application with sidebar
- `src/llm_agent.py` - Agent initialization functions
- `src/constants.py` - Configuration (uses env vars)

---

## ✅ Summary

The user API key feature provides:
- 🔒 **Security**: Keys stored only in session
- 🎯 **Flexibility**: Users use their own keys
- 💰 **Cost Control**: Users manage their own API costs
- 🚀 **Easy Deployment**: No server-side key management

**The application is now ready for multi-user deployment!** 🎉

