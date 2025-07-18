# Deployment Guide

This guide explains how to deploy LangGraph Agent as a free prototype.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy**
   ```bash
   ./scripts/deploy.sh
   # Choose option 1 (Railway)
   ```

3. **Set Environment Variables**
   In Railway dashboard, add:
   ```
   LLM_PROVIDER=azure
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_DEPLOYMENT=your_deployment
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   TAVILY_API_KEY=your_tavily_key
   NOTION_API_KEY=your_notion_key
   ```

### Option 2: Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Connect GitHub repository
   - Choose "Web Service"
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python backend/run.py`
   - Add environment variables

### Option 3: Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Deploy**
   ```bash
   flyctl auth login
   flyctl launch
   flyctl deploy
   ```

## 📋 Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] Frontend built (if applicable)
- [ ] Health check endpoint working (`/api/ping`)
- [ ] CORS configured for production domain
- [ ] API keys secured

## 🔧 Environment Variables Required

```bash
# LLM Provider (choose one)
LLM_PROVIDER=azure  # or openai

# Azure OpenAI (if using Azure)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# OpenAI (if using OpenAI)
OPENAI_API_KEY=your_key

# External APIs (optional)
TAVILY_API_KEY=your_tavily_key
NOTION_API_KEY=your_notion_key

# App Configuration
BACKEND_PORT=8000
FRONTEND_PORT=9002
```

## 🐳 Docker Deployment

For custom deployments:

```bash
# Build and run locally
docker-compose up --build

# Or build for production
docker build -t langgraph-agent .
docker run -p 8000:8000 --env-file .env langgraph-agent
```

## 🔍 Testing Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.railway.app/api/ping

# Provider status
curl https://your-app.railway.app/api/providers/status

# Conversations
curl https://your-app.railway.app/api/history/
```

## 💡 Tips for Free Tier

1. **Railway**: 500 hours/month free
2. **Render**: Always-on with free tier
3. **Fly.io**: Good for global deployment
4. **Optimize**: Use SQLite for simplicity
5. **Monitor**: Check usage to stay within limits

## 🚨 Security Notes

- Never commit API keys to Git
- Use environment variables for all secrets
- Enable HTTPS (automatic on most platforms)
- Consider rate limiting for public APIs

## 📞 Support

If you encounter issues:
1. Check the deployment logs
2. Verify environment variables
3. Test locally first
4. Check platform-specific documentation