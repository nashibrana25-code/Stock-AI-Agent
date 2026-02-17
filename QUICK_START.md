# 🚀 Quick Start - 100% FREE Setup

Your code is now on GitHub: https://github.com/nashibrana25-code/Stock-AI-Agent

## ✅ Already Done (LIVE):
- ✅ Frontend: https://frontend-blond-two-59.vercel.app
- ✅ API: https://asx-ai-investment-platform.vercel.app
- ✅ GitHub Actions workflow (runs AI agent every hour)

---

## 🆓 Complete FREE Setup (10 minutes)

### Step 1: Get FREE Database (Supabase) - 2 min

1. Go to https://supabase.com
2. Sign in with GitHub
3. Click "New project"
   - Name: `asx-ai-platform`
   - Database Password: Create & save it
   - Region: Choose closest
4. Wait 2 min for setup
5. Go to **Settings** → **Database** → **Connection string** → **URI**
6. Copy the full URL (looks like `postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`)

---

### Step 2: Get FREE Redis (Upstash) - 1 min

1. Go to https://upstash.com
2. Sign in with GitHub
3. Click "Create database"
   - Name: `asx-cache`
   - Type: Regional
4. Copy **UPSTASH_REDIS_REST_URL** from dashboard

---

### Step 3: Get FREE API Keys - 2 min

**Alpha Vantage:**
1. https://www.alphavantage.co/support/#api-key
2. Enter email → Get key

**NewsAPI:**
1. https://newsapi.org/register
2. Sign up → Copy key

---

### Step 4: Add GitHub Secrets - 3 min

1. Go to https://github.com/nashibrana25-code/Stock-AI-Agent/settings/secrets/actions
2. Click **New repository secret** for each:

| Secret Name | Value |
|-------------|-------|
| `DATABASE_URL` | Your Supabase PostgreSQL URL |
| `REDIS_URL` | Your Upstash Redis URL |
| `ALPHA_VANTAGE_API_KEY` | Your Alpha Vantage key |
| `NEWSAPI_KEY` | Your NewsAPI key |

---

### Step 5: Add Vercel Environment Variables - 2 min

1. Go to https://vercel.com/dashboard
2. Click your project: `asx-ai-investment-platform`
3. **Settings** → **Environment Variables**
4. Add the same 4 variables above
5. Click **Redeploy** to apply them

---

### Step 6: Test GitHub Actions - 1 min

1. Go to https://github.com/nashibrana25-code/Stock-AI-Agent/actions
2. Click **AI Agent - Run Every Hour**
3. Click **Run workflow** → **Run workflow** button
4. Wait ~2 minutes
5. Should see ✅ green checkmark

---

## 🎉 You're Done!

### What Happens Now:

**Every Hour (Automatic):**
- GitHub Actions runs AI agent
- Fetches latest ASX stock prices
- Generates AI predictions
- Creates recommendations
- Saves to database

**Anytime (On-Demand):**
- Users visit: https://frontend-blond-two-59.vercel.app
- See real-time data and recommendations
- Based on their capital ($50-$10,000)

**Cost:** $0/month forever! 💰

---

## 📊 View Your Live Platform

- **Dashboard:** https://frontend-blond-two-59.vercel.app
- **API Docs:** https://asx-ai-investment-platform.vercel.app/docs
- **API Health:** https://asx-ai-investment-platform.vercel.app/health
- **GitHub Actions:** https://github.com/nashibrana25-code/Stock-AI-Agent/actions

---

## 🔧 How to Update

Add more stocks, change logic, etc:

```powershell
# Make changes to code
cd C:\asx-ai-investment-platform

# Commit and push
git add .
git commit -m "Your changes"
git push origin master

# Auto-deploys to Vercel + GitHub Actions!
```

---

## 💡 Next Steps (Optional)

1. **Custom Domain:** Add your domain in Vercel (free)
2. **More Stocks:** Edit `services/data-ingestion/collectors/yahoo_collector.py`
3. **Better UI:** Customize `frontend/src/App.jsx`
4. **Email Alerts:** Add notification service
5. **User Login:** Enable Supabase Auth (free)

---

## 🆘 Need Help?

- **Actions failing?** Check secrets are added: https://github.com/nashibrana25-code/Stock-AI-Agent/settings/secrets/actions
- **API errors?** Check Vercel env vars: https://vercel.com/dashboard
- **Database issues?** Verify connection in Supabase dashboard

---

## 📈 Architecture (100% Free)

```
GitHub Actions (Hourly)
    ↓
Fetch Stock Data → Yahoo Finance + Alpha Vantage (FREE APIs)
    ↓
AI Analysis → Predict Prices
    ↓
Save to Database → Supabase PostgreSQL (FREE 500MB)
    ↓
Cache Results → Upstash Redis (FREE 10K commands/day)
    ↓
Done! ✅

User Visits Dashboard
    ↓
Vercel Frontend (FREE) → Calls API
    ↓
Vercel API (FREE) → Reads Database
    ↓
Shows Live Data! 🎉
```

**Total Cost: $0/month**

Enjoy your platform! 🚀
