import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from config import get_llm_config, LLMConfig, OpenAIConfig, AzureOpenAIConfig

def print_env_vars():
    """Print relevant environment variables for debugging."""
    print("\n=== Environment Variables ===")
    env_vars = {k: v for k, v in os.environ.items() 
               if k.startswith(('AZURE_', 'OPENAI_', 'LLM_'))}
    for key, value in env_vars.items():
        print(f"{key} = {'*' * 8 if 'KEY' in key or 'SECRET' in key else value}")
    print("==========================\n")
    return env_vars

def print_config_debug(config):
    """Print debug information about the configuration."""
    print("\n=== Configuration Debug ===")
    print(f"Config type: {type(config)}")
    print(f"Provider: {config.provider}")
    
    print("\nOpenAI Config:")
    if config.openai:
        print(f"  - Model: {config.openai.model}")
        print(f"  - API Key set: {'Yes' if config.openai.api_key else 'No'}")
    else:
        print("  - Not configured")
        
    print("\nAzure Config:")
    if config.azure:
        print(f"  - Endpoint: {config.azure.endpoint}")
        print(f"  - Deployment: {config.azure.deployment}")
        print(f"  - API Key set: {'Yes' if config.azure.api_key else 'No'}")
    else:
        print("  - Not configured")
    
    print("\nEnvironment variables in config:")
    pprint({k: v for k, v in os.environ.items() 
           if k.startswith(('AZURE_', 'OPENAI_', 'LLM_'))})
    print("==========================\n")

async def test_azure_connection():
    # Print environment variables for debugging
    print("\n=== Starting Azure OpenAI Connection Test ===")
    env_vars = print_env_vars()
    
    # Explicitly load .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"\nLoading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path, override=True)
    
    try:
        # Load configuration
        print("\nLoading configuration...")
        config = get_llm_config()
        
        # Print debug info
        print_config_debug(config)
        
        if config.provider != "azure":
            print(f"\n❌ ERRORE: LLM_PROVIDER non è impostato su 'azure' (attuale: {config.provider})")
            print("Per favore verifica il file .env o imposta LLM_PROVIDER=azure")
            print(f"Environment LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
            return
            
        if not config.azure:
            print("\n❌ ERRORE: Configurazione Azure non trovata")
            print("Assicurati di aver impostato le seguenti variabili d'ambiente:")
            print("- AZURE_OPENAI_API_KEY")
            print("- AZURE_OPENAI_ENDPOINT")
            print("- AZURE_OPENAI_DEPLOYMENT")
            print("- AZURE_OPENAI_API_VERSION (opzionale, default: 2023-05-15)")
            return
            
        print("\n✅ Configurazione Azure OpenAI rilevata:")
        print(f"- Endpoint: {config.azure.endpoint}")
        print(f"- Deployment: {config.azure.deployment}")
        print(f"- API Version: {config.azure.api_version}")
        print(f"- Model: {config.azure.model}")
        
        # Test connection by creating an instance of AzureChatOpenAI
        print("\nTesting connection to Azure OpenAI...")
        from langchain_openai import AzureChatOpenAI
        
        llm = AzureChatOpenAI(
            openai_api_version=config.azure.api_version,
            azure_deployment=config.azure.deployment,
            azure_endpoint=config.azure.endpoint,
            openai_api_key=config.azure.api_key,
            temperature=0,
            max_retries=2,
            timeout=10
        )
        
        # Test with a simple message
        print("Sending test message to Azure OpenAI...")
        response = await llm.ainvoke("Ciao, questo è un test di connessione. Dimmi 'funziona' se tutto va bene.")
        
        print("\n✅ Connessione riuscita!")
        print("Risposta dal modello:", response.content)
        
    except ImportError as e:
        print(f"\n❌ ERRORE: Pacchetto mancante - {e}")
        print("Per favore installa i pacchetti richiesti con:")
        print("pip install langchain-openai")
    except Exception as e:
        print(f"\n❌ ERRORE durante la connessione ad Azure OpenAI: {str(e)}")
        print("\nControlla che:")
        print("1. La chiave API Azure sia corretta")
        print("2. L'endpoint sia corretto e accessibile")
        print("3. Il deployment sia stato creato e sia attivo")
        print("4. La regione dell'endpoint corrisponda alla chiave API")
    finally:
        print("\nTest completato.")
        


if __name__ == "__main__":
    asyncio.run(test_azure_connection())