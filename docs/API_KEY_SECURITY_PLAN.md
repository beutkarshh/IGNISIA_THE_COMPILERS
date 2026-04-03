# 🔐 API Key Security Plan - Protecting Your Last Gemini Key

## 🚨 IMMEDIATE ACTIONS (Do This Now!)

### 1. **Secure Your Last Key**

**Step 1: Store it safely OUTSIDE the project**
```bash
# Create a secure location OUTSIDE your project
mkdir C:\secure-keys
echo "GEMINI_API_KEY=your_last_key_here" > C:\secure-keys\.env.secure
```

**Step 2: Update your project to reference it**
```bash
# In your project .env, reference the secure location:
GEMINI_API_KEY_PATH=C:\secure-keys\.env.secure
```

### 2. **Enable API Key Restrictions (CRITICAL)**

Go to [Google AI Studio](https://aistudio.google.com/app/apikey):
1. **IP Restrictions**: Add only your current IP
2. **Referrer Restrictions**: Add your domain if deploying
3. **Rate Limits**: Set conservative limits
4. **Monitoring**: Enable usage alerts

### 3. **Backup Strategy**
- Take a screenshot of the API key (store securely offline)
- Write it down on paper (store in safe place)
- Save in password manager (1Password, LastPass, etc.)

---

## 🛡️ PROTECTION STRATEGIES

### Option 1: **Environment Variable Outside Project**

**Create secure env loader:**
```python
# utils/secure_env.py
import os
from pathlib import Path

def load_secure_gemini_key():
    """Load Gemini key from secure location outside project."""
    secure_paths = [
        os.getenv('GEMINI_API_KEY'),  # Direct env var
        r'C:\secure-keys\.env',       # Windows secure location
        Path.home() / '.secure' / '.env',  # User home secure
    ]
    
    for path in secure_paths:
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        return line.split('=', 1)[1].strip()
    
    raise ValueError("Secure Gemini API key not found!")
```

### Option 2: **Azure Key Vault** (Recommended for Production)

```bash
# Install Azure Key Vault SDK
pip install azure-keyvault-secrets azure-identity
```

```python
# Store key in Azure Key Vault
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_gemini_key_from_vault():
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
    secret = client.get_secret("gemini-api-key")
    return secret.value
```

### Option 3: **Local Windows Credential Store**

```python
# Store in Windows Credential Manager
import keyring

# Store once:
keyring.set_password("gemini-api", "your-app", "your_api_key_here")

# Retrieve:
def get_gemini_key():
    return keyring.get_password("gemini-api", "your-app")
```

### Option 4: **Environment-Only (No Files)**

```bash
# Set system environment variable (Windows)
setx GEMINI_API_KEY "your_key_here"

# Or in PowerShell (session only)
$env:GEMINI_API_KEY="your_key_here"
```

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: **Immediate Protection** (Do Now)

1. **Move key outside project**
   - Copy to `C:\secure-keys\.env`
   - Remove from project `.env`
   - Add secure path to gitignore

2. **Update project code**
   - Modify key loading in `agents/tools.py`
   - Test with secure loading

3. **Enable API restrictions**
   - IP allowlist
   - Rate limiting
   - Usage alerts

### Phase 2: **Enhanced Security** (Next)

1. **Implement secure loader**
2. **Add error handling for missing keys**
3. **Create fallback mechanisms**
4. **Set up monitoring**

### Phase 3: **Production Ready** (Future)

1. **Azure Key Vault integration**
2. **Automated key rotation**
3. **Multi-environment support**
4. **Audit logging**

---

## 📊 MONITORING & ALERTS

### Google AI Studio Dashboard

1. **Usage Monitoring**
   - Check daily usage
   - Set alerts at 80% of quota
   - Monitor for unusual patterns

2. **Security Events**
   - Track API calls by IP
   - Monitor for unauthorized access
   - Review error patterns

### Custom Monitoring

```python
# Add to your code
import logging
from datetime import datetime

def log_api_usage(operation, success=True):
    logging.info(f"Gemini API: {operation}, Success: {success}, Time: {datetime.now()}")
```

---

## 🚫 WHAT TO AVOID

### Never Do This Again:
- ❌ Put API key in `.env` file
- ❌ Commit `.env` to git
- ❌ Share key in chat/screenshots
- ❌ Paste key in VS Code when Copilot is active
- ❌ Store in browser or cloud sync folders
- ❌ Use key without IP restrictions

### Safe Practices:
- ✅ Store outside project directory
- ✅ Use environment variables only
- ✅ Enable all possible restrictions
- ✅ Monitor usage regularly
- ✅ Have backup storage (offline)

---

## 🆘 EMERGENCY PLAN

### If Key Gets Compromised:
1. **Immediately revoke** in Google AI Studio
2. **Generate replacement** (if available)
3. **Update all environments**
4. **Review access logs**
5. **Implement stricter security**

### If No More Keys Available:
1. **Contact Google Support** for additional quota
2. **Use alternative APIs** (OpenAI, Anthropic)
3. **Implement local models** (Ollama)
4. **Request team/organization keys**

---

## 🔄 ALTERNATIVE SOLUTIONS

### Option A: **OpenAI Integration**
```python
# Fallback to OpenAI GPT-4
import openai

def fallback_to_openai(prompt):
    client = openai.OpenAI(api_key="your_openai_key")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Option B: **Local Models** (No API Key Needed)
```python
# Use Ollama for local inference
def use_local_model(prompt):
    import ollama
    response = ollama.chat(model='llama2', messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']
```

### Option C: **Rule-Based Fallback**
Your agents already work without Gemini for:
- SIRS criteria detection
- qSOFA scoring  
- Lab trend analysis
- Basic risk assessment

---

## 📋 ACTION CHECKLIST

**Immediate (Next 10 minutes):**
- [ ] Move API key to secure location outside project
- [ ] Remove key from project `.env`
- [ ] Add IP restrictions in Google AI Studio
- [ ] Take screenshot backup of key
- [ ] Test secure loading

**Today:**
- [ ] Implement secure key loader
- [ ] Set up usage monitoring
- [ ] Enable rate limiting
- [ ] Create offline backup
- [ ] Test entire system

**This Week:**
- [ ] Implement fallback mechanisms
- [ ] Add comprehensive error handling
- [ ] Set up alerts and monitoring
- [ ] Document security procedures
- [ ] Train team on best practices

---

## 🎯 RECOMMENDED APPROACH

**For your last key, I recommend:**

1. **Immediate**: Store in Windows Credential Manager
2. **Short-term**: Implement secure file loading outside project
3. **Long-term**: Azure Key Vault integration
4. **Backup**: Keep offline copy in password manager

This gives you maximum protection while keeping development smooth.

---

**Would you like me to help you implement any of these security measures right now?**