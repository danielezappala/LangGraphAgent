import asyncio, json, os, pathlib
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# 1. carico l'env del plugin dal file di config
cfg_path = pathlib.Path("~/.codeium/windsurf/mcp_config.json").expanduser()
env = json.loads(cfg_path.read_text())["mcpServers"]["notion-mcp-server"]["env"]

# 2. preparo i parametri del processo stdio
params = StdioServerParameters(
    command="npx",
    args=["-y", "@notionhq/notion-mcp-server"],
    env=env                     # ← passa l'intero dict così com'è
)

async def main():
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print(await s.list_tools())

asyncio.run(main())
