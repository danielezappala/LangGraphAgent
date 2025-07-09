import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

def pretty_print_messages(messages: list[BaseMessage]):
    """
    Stampa una lista di messaggi con indentazione e formattazione per una migliore leggibilità,
    distinguendo tra i vari tipi di messaggio.
    """
    for i, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            print(f"\n👤 USER:")
            print(f"{message.content}")
        
        elif isinstance(message, AIMessage):
            print(f"\n🤖 ASSISTANT:")
            if message.content:
                print(f"{message.content}")
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print("  Tool Calls:")
                for tool_call in message.tool_calls:
                    try:
                        args = json.dumps(tool_call.get('args', {}), indent=2)
                        print(f"    - Tool: {tool_call.get('name')}\n      Args:\n{args}")
                    except (TypeError, json.JSONDecodeError):
                        print(f"    - Tool: {tool_call.get('name')}, Args: {tool_call.get('args')}")

        elif isinstance(message, ToolMessage):
            print(f"\n  - TOOL OUTPUT (ID: {message.tool_call_id})-")
            try:
                content_json = json.loads(message.content)
                pretty_content = json.dumps(content_json, indent=2)
                print(f"{pretty_content}")
            except (json.JSONDecodeError, TypeError):
                print(f"    {message.content}")
        else:
            print(f"\n[UNKNOWN MESSAGE TYPE] {type(message)}")
            print(f"{message}")
        
        if i < len(messages) - 1:
            print("""----------------------------------------""")
