# 🚀 Deploy to Vercel - Make Your Platform Live!

## Quick Deploy (2 Minutes)

### Step 1: Install Vercel CLI

```powershell
npm install -g vercel
```

### Step 2: Deploy Backend API

```powershell
cd C:\asx-ai-investment-platform

# Login to Vercel
vercel login

# Deploy API
vercel --prod
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No
- **Project name?** asx-ai-platform
- **Directory?** ./
- **Override settings?** No

✅ Your API will be live at: `https://asx-ai-platform.vercel.app`

### Step 3: Deploy Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Deploy
vercel --prod
```

✅ Your dashboard will be live at: `https://asx-ai-platform-frontend.vercel.app`

---

## Alternative: Deploy Both Together

### Option A: Vercel (Frontend + Backend)

1. **Push to GitHub:**
```powershell
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/asx-ai-platform.git
git push -u origin main
```

2. **Connect to Vercel:**
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel auto-detects and deploys!

### Option B: Railway (Better for AI Agent)

Railway is perfect for the 24/7 AI agent background worker.

```powershell
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

**Cost:** $5-10/month
**Result:** Your AI agent runs 24/7 at a public URL!

---

## Recommended Architecture (Best of Both Worlds)

**Frontend:** Vercel (FREE ✨)
- Static site hosting
- Global CDN
- Automatic HTTPS
- Custom domain support

**Backend API:** Vercel Serverless (FREE tier)
- API endpoints
- Serverless functions
- Auto-scaling

**AI Agent:** Railway/Render ($10/month)
- 24/7 background worker
- Continuous stock monitoring
- Database included

**Database:** 
- Supabase (FREE PostgreSQL)
- Upstash (FREE Redis)

**Total Cost:** $0-10/month! 🎉

---

## Setup for This Architecture

### 1. Deploy Frontend to Vercel (FREE)

```powershell
cd frontend
vercel --prod
```

Your dashboard: `https://your-site.vercel.app`

### 2. Deploy API to Vercel (FREE)

```powershell
cd C:\asx-ai-investment-platform
vercel --prod
```

Your API: `https://your-api.vercel.app`

### 3. Deploy AI Agent to Railway

```powershell
# Create railway.json in project root
# (already created for you)

railway login
railway init
railway up

# Add environment variables in Railway dashboard:
# - ALPHA_VANTAGE_API_KEY
# - NEWSAPI_KEY
# - DATABASE_URL (from Supabase)
```

### 4. Setup Free Database (Supabase)

1. Go to https://supabase.com
2. Create new project (FREE)
3. Copy connection string
4. Add to Vercel & Railway environment variables:
   ```
   DATABASE_URL=postgresql://...
   ```

### 5. Setup Free Redis (Upstash)

1. Go to https://upstash.com
2. Create Redis database (FREE)
3. Copy connection URL
4. Add to environment variables:
   ```
   REDIS_URL=redis://...
   ```

---

## Environment Variables (Add to Vercel)

In Vercel dashboard, add these:

```
# API Keys
ALPHA_VANTAGE_API_KEY=your_key
NEWSAPI_KEY=your_key

# Database
DATABASE_URL=postgresql://your-supabase-url
REDIS_URL=redis://your-upstash-url

# URLs
FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_URL=https://your-api.vercel.app

# Security
SECRET_KEY=your-random-secret-key
```

---

## Custom Domain (Optional)

### Add Your Domain to Vercel:

1. Buy domain from Namecheap/GoDaddy ($10/year)
2. In Vercel project settings → Domains
3. Add: `www.mysmartstocks.com`
4. Update DNS records as instructed
5. SSL certificate auto-generated! 🔒

---

## Deploy Commands Summary

```powershell
# One-time setup
npm install -g vercel
npm install -g @railway/cli

# Deploy frontend (FREE)
cd frontend
vercel --prod

# Deploy API (FREE)
cd ..
vercel --prod

# Deploy AI Agent (24/7 worker)
railway up

# Update deployment
vercel --prod  # Redeploy on changes
```

---

## Access Your Live Platform

After deployment:

✅ **Frontend:** https://asx-ai-platform.vercel.app
- Users get recommendations
- Real-time stock data
- Portfolio tracking

✅ **API:** https://asx-ai-platform-api.vercel.app
- RESTful endpoints
- WebSocket support
- Auto-generated docs at `/api/docs`

✅ **AI Agent:** https://asx-agent.railway.app
- Runs 24/7 in background
- Updates data continuously
- Sends real-time alerts

---

## Monitoring Your Live Platform

### Vercel Dashboard
- Visit https://vercel.com/dashboard
- View deployment logs
- Monitor performance
- Check analytics

### Railway Dashboard
- Visit https://railway.app/dashboard
- View AI agent logs
- Monitor CPU/Memory
- Restart if needed

---

## Scaling & Performance

**Free Tier Limits:**
- Vercel: 100GB bandwidth/month
- Railway: 500 hours/month ($5 upgrade for unlimited)
- Supabase: 500MB database, 2GB bandwidth

**When to upgrade:**
- 1000+ users: Upgrade Railway to Pro ($20/mo)
- Heavy traffic: Add CDN (Cloudflare - FREE)
- More data: Upgrade Supabase ($25/mo for 8GB)

---

## Troubleshooting

**Build fails on Vercel:**
```powershell
# Check vercel.json is correct
# Ensure requirements.txt has all dependencies
vercel logs
```

**AI Agent not running:**
```powershell
# Check Railway logs
railway logs
# Restart
railway restart
```

**Database connection issues:**
```powershell
# Verify DATABASE_URL in environment variables
# Check Supabase dashboard for connection string
```

---

## Next Steps

1. ✅ Deploy to Vercel (takes 2 minutes)
2. ✅ Test your live URL
3. ✅ Add custom domain (optional)
4. ✅ Share with users!

**Your platform is now accessible 24/7 from anywhere in the world! 🌍**

Run this now:
```powershell
cd C:\asx-ai-investment-platform
vercel --prod
```
