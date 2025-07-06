import json
from datetime import datetime
from backend.config import HISTORY_FILE

class PersistentMemory:
    def __init__(self, agent_name: str):
        self.filename = f"backend/history_{agent_name}.json"
        self.history = self.load()

    def add_message(self, role, content, tokens):
        self.history.append({
            "role": role,
            "content": content,
            "tokens": tokens,
            "date": datetime.now().date().isoformat()
        })

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def get_history(self, with_metadata=False):
        if with_metadata:
            return self.history
        return [{"role": m["role"], "content": m["content"]} for m in self.history] 