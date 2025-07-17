import os
import asyncio
from pprint import pprint

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()
# Legacy config import removed - now using centralized EnvironmentLoader

def print_env_vars():
    """Print relevant environment variables for debugging."""
    print("\n=== Environment Variables ===")
    env_vars = {k: v for k, v in os.environ.items() 
               if k.startswith(('AZURE_', 'OPENAI_', 'LLM_'))}
    for key, value in env_vars.items():
        print(f"{key} = {'*' * 8 if 'KEY' in key or 'SECRET' in key else value}")
    print("==========================\n")
    return env_vars


async def test_azure_connection():
    # Print environment variables for debugging
    print("\n=== Starting Azure OpenAI Connection Test ===")
    env_vars = print_env_vars()
    
    # Environment variables already loaded by centralized loader
    
    try:
        # Load configuration using centralized loader
        print("\nLoading configuration...")
        provider = EnvironmentLoader.get_llm_provider()
        azure_config = EnvironmentLoader.get_azure_config()
        
        if not provider or provider.lower() != "azure":
            print(f"\n❌ ERRORE: LLM_PROVIDER non è impostato su 'azure' (attuale: {provider})")
            print("Per favore verifica il file .env o imposta LLM_PROVIDER=azure")
            return
            
        if not azure_config['api_key'] or not azure_config['endpoint']:
            print("\n❌ ERRORE: Configurazione Azure non trovata")
            print("Assicurati di aver impostato le seguenti variabili d'ambiente:")
            print("- AZURE_OPENAI_API_KEY")
            print("- AZURE_OPENAI_ENDPOINT")
            print("- AZURE_OPENAI_DEPLOYMENT")
            print("- AZURE_OPENAI_API_VERSION (opzionale, default: 2023-05-15)")
            return
            
        print("\n✅ Configurazione Azure OpenAI rilevata:")
        print(f"- Endpoint: {azure_config['endpoint']}")
        print(f"- Deployment: {azure_config['deployment']}")
        print(f"- API Version: {azure_config['api_version']}")
        print(f"- Model: {azure_config['model']}")
        
        # Test connection by creating an instance of AzureChatOpenAI
        print("\nTesting connection to Azure OpenAI...")
        from langchain_openai import AzureChatOpenAI
        
        llm = AzureChatOpenAI(
            openai_api_version=azure_config['api_version'],
            azure_deployment=azure_config['deployment'],
            azure_endpoint=azure_config['endpoint'],
            openai_api_key=azure_config['api_key'],
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