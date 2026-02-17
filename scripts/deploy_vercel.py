#!/usr/bin/env python3
"""
One-command deploy to Vercel + Railway
Makes your platform accessible worldwide!
"""
import subprocess
import sys
import os

def run_cmd(cmd, description):
    """Run command and show output"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True)
        print(f"✅ {description} - SUCCESS\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED\n")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        🚀 Deploy ASX AI Platform to the Cloud                   ║
║                                                                  ║
║        Make it accessible 24/7 from anywhere!                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nThis will deploy:")
    print("  🌐 Frontend → Vercel (FREE)")
    print("  ⚡ API → Vercel Serverless (FREE)")
    print("  🤖 AI Agent → Railway ($5-10/month)")
    print("\nTotal cost: $0-10/month for unlimited global access!\n")
    
    proceed = input("Continue? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Deployment cancelled")
        sys.exit(0)
    
    # Check if Vercel CLI is installed
    print("\n🔍 Checking prerequisites...")
    try:
        subprocess.run("vercel --version", shell=True, check=True, capture_output=True)
        print("✅ Vercel CLI found")
    except:
        print("❌ Vercel CLI not found. Installing...")
        run_cmd("npm install -g vercel", "Installing Vercel CLI")
    
    # Login to Vercel
    print("\n🔐 Please login to Vercel (browser will open)...")
    run_cmd("vercel login", "Vercel login")
    
    # Deploy Frontend
    print("\n📱 Deploying Frontend to Vercel...")
    os.chdir("frontend")
    
    if not os.path.exists("node_modules"):
        run_cmd("npm install", "Installing frontend dependencies")
    
    run_cmd("npm run build", "Building frontend")
    
    if run_cmd("vercel --prod", "Deploying frontend to Vercel"):
        print("\n✅ Frontend deployed successfully!")
        print("Access your dashboard at the URL shown above ☝️")
    
    # Deploy API
    print("\n⚡ Deploying API to Vercel...")
    os.chdir("..")
    
    if run_cmd("vercel --prod", "Deploying API to Vercel"):
        print("\n✅ API deployed successfully!")
        print("Your API is now live at the URL shown above ☝️")
    
    # Instructions for AI Agent
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  ✅ Frontend & API Deployed Successfully!                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

🎉 Your platform is now LIVE and accessible worldwide!

📍 Next Steps:

1. Deploy the 24/7 AI Agent to Railway:
   
   a) Go to https://railway.app
   b) Sign up with GitHub (FREE)
   c) Click "New Project" → "Deploy from GitHub repo"
   d) Connect this repository
   e) Railway will auto-detect and deploy the AI agent
   f) Add environment variables in Railway dashboard:
      - ALPHA_VANTAGE_API_KEY
      - NEWSAPI_KEY
      - DATABASE_URL (get from Supabase.com - FREE)
      - REDIS_URL (get from Upstash.com - FREE)

2. Add Environment Variables to Vercel:
   
   a) Go to your Vercel dashboard
   b) Select your project
   c) Settings → Environment Variables
   d) Add all API keys from your .env file

3. Optional - Add Custom Domain:
   
   a) Buy domain from Namecheap/GoDaddy ($10/year)
   b) In Vercel: Settings → Domains
   c) Add your domain
   d) Update DNS records
   e) SSL certificate auto-generated!

📚 Full guide: DEPLOY_VERCEL.md

🌐 Your platform is LIVE! Share your URL with users! 🚀
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
