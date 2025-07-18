#!/bin/bash
"""
Script di deploy per LangGraph Agent
Supporta Railway, Render, e Fly.io
"""

set -e

echo "🚀 LangGraph Agent Deploy Script"
echo "================================"

# Check if we're in the right directory
if [ ! -f "backend/run.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to deploy to Railway
deploy_railway() {
    echo "🚂 Deploying to Railway..."
    
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    railway login
    railway init
    railway up
    
    echo "✅ Deployed to Railway!"
    echo "🌐 Your app will be available at the URL shown above"
}

# Function to deploy to Render
deploy_render() {
    echo "🎨 Deploying to Render..."
    echo "Please follow these steps:"
    echo "1. Push your code to GitHub"
    echo "2. Go to https://render.com"
    echo "3. Connect your GitHub repository"
    echo "4. Choose 'Web Service'"
    echo "5. Set build command: 'pip install -r requirements.txt'"
    echo "6. Set start command: 'python backend/run.py'"
    echo "7. Add your environment variables"
}

# Function to deploy to Fly.io
deploy_fly() {
    echo "🪰 Deploying to Fly.io..."
    
    if ! command -v flyctl &> /dev/null; then
        echo "Installing Fly CLI..."
        curl -L https://fly.io/install.sh | sh
    fi
    
    flyctl auth login
    flyctl launch
    flyctl deploy
    
    echo "✅ Deployed to Fly.io!"
}

# Main menu
echo "Choose your deployment platform:"
echo "1) Railway (Recommended)"
echo "2) Render"
echo "3) Fly.io"
echo "4) Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        deploy_railway
        ;;
    2)
        deploy_render
        ;;
    3)
        deploy_fly
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment completed!"
echo "📝 Don't forget to:"
echo "   - Set your environment variables in the platform dashboard"
echo "   - Test your deployed application"
echo "   - Share the URL with your users!"