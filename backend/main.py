from dotenv import load_dotenv
load_dotenv()

from backend.config import HISTORY_FILE, SYSTEM_PROMPT_FILE, MODEL_NAME, MIN_RESPONSE_TOKENS
from backend.persistent_memory import PersistentMemory
from backend.llm_utils import LLMClient
from backend.agent import ConversationalAgent
import json

def load_system_prompt(filename):
    with open(filename, "r") as f:
        return json.load(f)

def main():
    memory = PersistentMemory(HISTORY_FILE)
    llm_client = LLMClient(MODEL_NAME, MIN_RESPONSE_TOKENS)
    system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
    agent = ConversationalAgent(memory, llm_client, system_prompt)
    agent.run()

if __name__ == "__main__":
    main() 