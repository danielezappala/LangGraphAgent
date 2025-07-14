import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Load environment variables
load_dotenv()

async def test_azure_connection():
    print("\n=== Testing Azure OpenAI Connection ===")
    
    # Get configuration from environment
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")
    
    if not all([api_key, endpoint, deployment]):
        print("\n❌ Missing required Azure OpenAI configuration in .env file")
        print("Please ensure the following are set:")
        print("- AZURE_OPENAI_API_KEY")
        print("- AZURE_OPENAI_ENDPOINT")
        print("- AZURE_OPENAI_DEPLOYMENT")
        return
    
    try:
        # Initialize the client
        client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        # Test a simple completion
        print("\nSending test request to Azure OpenAI...")
        response = await client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say 'hello'"}],
            max_tokens=10
        )
        
        print("\n✅ Successfully connected to Azure OpenAI!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Error connecting to Azure OpenAI: {str(e)}")
        print("\nPlease check the following:")
        print("1. Your Azure OpenAI API key is correct")
        print("2. The endpoint URL is correct and accessible")
        print("3. The deployment name exists in your Azure OpenAI resource")
        print("4. Your Azure OpenAI resource is in the correct region")
        print("5. Your network allows outbound connections to Azure OpenAI")

if __name__ == "__main__":
    asyncio.run(test_azure_connection())
