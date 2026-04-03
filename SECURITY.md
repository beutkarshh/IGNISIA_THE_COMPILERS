# Security Guidelines

## 🔐 API Key Management

### Never Commit Secrets
- `.env` is in `.gitignore` - keep it that way
- Only commit `.env.example` with placeholder values
- Use `git log -p` to check for accidental commits

### If a Key is Exposed:
1. **Immediately revoke** the key in the provider's dashboard
2. **Generate a new key** 
3. **Update** your `.env` file
4. **Check git history**: `git log -p -S "partial_key_string"`
5. If committed, use `git filter-branch` or contact GitHub support

### Where Keys Can Leak:
- ❌ Committing `.env` to git
- ❌ Sharing in chat/Discord/Slack
- ❌ Screenshots with visible keys
- ❌ Pasting in GitHub issues/PRs
- ❌ Error logs with environment variables
- ❌ Public deployment configs
- ❌ VS Code sync settings (if not careful)

### Best Practices:
- ✅ Use `.env` for local development
- ✅ Use environment variables in production
- ✅ Rotate keys periodically
- ✅ Use different keys for dev/staging/prod
- ✅ Enable API key restrictions (IP allowlists, rate limits)
- ✅ Monitor API usage for anomalies

## 🔗 Key Rotation Guides

### Gemini API
- Dashboard: https://aistudio.google.com/app/apikey
- Revoke old key → Create new key → Update `.env`

### Supabase
- Dashboard: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
- Settings → API → Service Role Key → Reset

### Firebase
- Console: https://console.firebase.google.com/
- Project Settings → Service Accounts → Generate New Key

## 🚨 Incident Response

If you discover a leaked key:
1. Revoke it IMMEDIATELY (within minutes)
2. Check for unauthorized usage
3. Generate replacement
4. Update all environments
5. Document what happened

## 📝 Monitoring

Set up usage alerts:
- Gemini: Check quota usage in Google Cloud Console
- Supabase: Monitor usage dashboard
- Enable billing alerts for unexpected costs

---

**Remember**: When in doubt, rotate the key. It's free and takes 2 minutes.
