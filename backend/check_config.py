# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

def check_config():
    print("\n=== Azure OpenAI Configuration ===")
    
    # Get configuration from centralized environment loader
    azure_config = EnvironmentLoader.get_azure_config()
    provider = EnvironmentLoader.get_llm_provider()
    
    # Get and mask the API key
    api_key = azure_config['api_key']
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "Not set"
    
    print(f"Provider: {provider or 'Not set'}")
    print(f"API Key: {masked_key}")
    print(f"Endpoint: {azure_config['endpoint'] or 'Not set'}")
    print(f"Deployment: {azure_config['deployment'] or 'Not set'}")
    print(f"API Version: {azure_config['api_version'] or 'Not set'}")
    
    # Check for required variables
    required_configs = {
        'api_key': azure_config['api_key'],
        'endpoint': azure_config['endpoint'],
        'deployment': azure_config['deployment']
    }
    missing_vars = [var for var, value in required_configs.items() if not value]
    
    if missing_vars:
        print("\n❌ Missing required configuration values:")
        for var in missing_vars:
            print(f"- {var.upper()}")
    else:
        print("\n✅ All required configuration values are set")
        
        # Check endpoint format
        endpoint = azure_config['endpoint'] or ""
        if not endpoint.startswith("https://") or ".openai.azure.com" not in endpoint:
            print("\n⚠️  Warning: The endpoint format doesn't match the expected pattern.")
            print("It should be in the format: https://YOUR_RESOURCE_NAME.openai.azure.com/")

if __name__ == "__main__":
    check_config()
