import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_config():
    print("\n=== Azure OpenAI Configuration ===")
    
    # Get and mask the API key
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "Not set"
    
    print(f"Provider: {os.getenv('LLM_PROVIDER', 'Not set')}")
    print(f"API Key: {masked_key}")
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'Not set')}")
    print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT', 'Not set')}")
    print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION', 'Not set')}")
    
    # Check for required variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
    else:
        print("\n✅ All required environment variables are set")
        
        # Check endpoint format
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if not endpoint.startswith("https://") or ".openai.azure.com" not in endpoint:
            print("\n⚠️  Warning: The endpoint format doesn't match the expected pattern.")
            print("It should be in the format: https://YOUR_RESOURCE_NAME.openai.azure.com/")

if __name__ == "__main__":
    check_config()
