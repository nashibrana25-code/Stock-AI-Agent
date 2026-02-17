# ASX AI Investment Platform - 24/7 Cloud Deployment Guide

## 🌐 Making Your Platform Accessible Worldwide

Your platform can be deployed to run 24/7 and accessed from anywhere via a web URL.

---

## Quick Deploy Options

### Option 1: AWS (Recommended for Production)

**Cost:** ~$50-100/month for small-medium usage

```powershell
# Install AWS CLI
winget install Amazon.AWSCLI

# Configure AWS credentials
aws configure

# Deploy everything
python scripts/deploy.py
```

**Your platform will be accessible at:**
- API: `https://api.yourplatform.com`
- Frontend: `https://yourplatform.com`

---

### Option 2: Azure

**Cost:** ~$40-80/month

```powershell
# Install Azure CLI
winget install Microsoft.AzureCLI

# Login
az login

# Deploy
python scripts/deploy.py
```

---

### Option 3: Free/Low-Cost Option

**Frontend:** Deploy to Vercel/Netlify (FREE)
**Backend:** Railway/Render ($5-10/month)

```powershell
# Deploy frontend to Vercel
cd frontend
npm install -g vercel
vercel deploy --prod

# Deploy backend to Railway
# Visit railway.app and connect your GitHub repo
```

---

## Architecture (Cloud Deployment)

```
Internet Users
    ↓
CloudFlare/CDN (Optional)
    ↓
Load Balancer
    ↓
┌─────────────┬──────────────┬──────────────┐
│             │              │              │
│   Web App   │   API Server │  AI Agent    │
│  (React)    │  (FastAPI)   │ (24/7 Worker)│
│             │              │              │
└─────────────┴──────────────┴──────────────┘
         ↓           ↓              ↓
    ┌────────────────────────────────────┐
    │     Cloud Database (PostgreSQL)     │
    │     Redis Cache                     │
    │     Message Queue (Kafka/RabbitMQ)  │
    └────────────────────────────────────┘
```

---

## Deployment Steps (Detailed)

### Step 1: Prepare Environment

```powershell
# Navigate to project
cd C:\asx-ai-investment-platform

# Create production .env file
cp .env.example .env.production

# Edit with production settings
notepad .env.production
```

Add:
```env
APP_ENV=production
DEBUG=false

# Your production database
DB_HOST=your-db-host.rds.amazonaws.com
DB_PASSWORD=your-secure-password

# API Keys
ALPHA_VANTAGE_API_KEY=your_key
NEWSAPI_KEY=your_key

# Domain
FRONTEND_URL=https://yourplatform.com
BACKEND_URL=https://api.yourplatform.com
```

### Step 2: Build Docker Images

```powershell
# Build all services
docker-compose -f docker-compose.prod.yml build

# Test locally first
docker-compose -f docker-compose.prod.yml up
```

### Step 3: Deploy to Cloud

#### AWS ECS Deployment

```powershell
# Install AWS CDK
npm install -g aws-cdk

# Deploy infrastructure
cd infrastructure/aws
cdk deploy --all
```

This creates:
- ECS Cluster for containers
- RDS PostgreSQL database
- ElastiCache Redis
- Application Load Balancer
- CloudWatch monitoring
- Auto-scaling groups

#### Or use the automated script:

```powershell
python scripts/deploy.py
# Select option 1 (AWS)
```

### Step 4: Deploy Frontend

```powershell
cd frontend

# Build production version
npm run build

# Deploy to Vercel
vercel --prod

# Or Netlify
netlify deploy --prod --dir=build
```

### Step 5: Configure Domain

1. **Buy a domain** (e.g., from Namecheap, GoDaddy)
   - Example: `mysmartstocks.com`

2. **Point DNS to your deployment:**

   For AWS:
   ```
   Type: A
   Name: @
   Value: Your-ALB-Address.elb.amazonaws.com
   
   Type: CNAME
   Name: api
   Value: Your-API-ALB.elb.amazonaws.com
   ```

   For Vercel (Frontend):
   ```
   - Go to Vercel dashboard
   - Add custom domain
   - Update DNS settings as instructed
   ```

3. **SSL is automatic!** 
   - AWS: Uses ACM (free)
   - Vercel/Netlify: Auto Let's Encrypt

---

## 🤖 Starting the 24/7 AI Agent

Once deployed, your AI agent runs automatically:

```python
# The agent is deployed as a separate container/service
# It runs continuously in the background

# Check status:
curl https://api.yourplatform.com/health

# Monitor AI agent:
curl https://api.yourplatform.com/api/v1/admin/agent/status
```

The AI agent:
- ✅ Updates stock prices every minute
- ✅ Generates predictions every 30 minutes
- ✅ Creates recommendations hourly
- ✅ Monitors portfolios 24/7
- ✅ Sends real-time alerts via WebSocket

---

## Access Your Platform

After deployment:

1. **Web Dashboard:** `https://yourplatform.com`
   - Users can get recommendations
   - View live stock data
   - Monitor portfolios

2. **API:** `https://api.yourplatform.com/api/docs`
   - RESTful API documentation
   - WebSocket endpoints
   - Authentication

3. **Admin Panel:** `https://yourplatform.com/admin`
   - Monitor AI agent status
   - View system metrics
   - Manage users

---

## Monitoring & Management

### CloudWatch (AWS) / Azure Monitor

```powershell
# View logs
aws logs tail /ecs/asx-platform --follow

# View metrics
aws cloudwatch get-metric-statistics
```

### Built-in Monitoring

Access Grafana dashboard:
- URL: `https://monitoring.yourplatform.com`
- Default login: admin/admin

Metrics tracked:
- API response times
- AI prediction accuracy
- Stock price update frequency
- User activity
- Error rates

---

## Scaling

### Auto-Scaling Configuration

The platform automatically scales based on:
- CPU usage > 70%
- Memory usage > 80%
- Request rate > 1000/min

Configure in `infrastructure/aws/auto-scaling.json`

---

## Costs Breakdown

### AWS (Production)
- **ECS Tasks:** $30/month (2 tasks)
- **RDS Database:** $25/month (t3.micro)
- **Load Balancer:** $20/month
- **Data Transfer:** $10/month
- **Total:** ~$85/month

### Budget Option
- **Frontend:** Vercel (FREE)
- **Backend:** Railway ($10/month)
- **Database:** Supabase (FREE tier)
- **Total:** $10/month

---

## Security Checklist

- [x] HTTPS enabled (SSL certificates)
- [x] API authentication (JWT tokens)
- [x] Rate limiting configured
- [x] Database encrypted
- [x] Environment variables secured
- [x] CORS properly configured
- [x] DDoS protection (CloudFlare)

---

## Maintenance

### Weekly
- Check error logs
- Review AI prediction accuracy
- Monitor API usage

### Monthly
- Update dependencies
- Retrain ML models
- Review and optimize costs

### Quarterly
- Security audit
- Performance optimization
- Feature updates

---

## Troubleshooting

### AI Agent Not Running
```powershell
# Check container status
docker ps | grep ai-agent

# View logs
docker logs asx-ai-agent

# Restart
docker restart asx-ai-agent
```

### Database Connection Issues
```powershell
# Test connection
psql -h your-db.rds.amazonaws.com -U asx_user -d asx_platform

# Check security groups (AWS)
aws ec2 describe-security-groups
```

---

## Next Steps

1. ✅ Deploy to cloud
2. ✅ Configure custom domain
3. ✅ Test AI agent functionality
4. ✅ Set up monitoring alerts
5. ✅ Share your platform URL!

---

## Support & Resources

- AWS Documentation: https://docs.aws.amazon.com/ecs/
- Vercel Documentation: https://vercel.com/docs
- Your platform docs: `https://yourplatform.com/docs`

**Your platform is now live and accessible 24/7 from anywhere in the world! 🚀**
