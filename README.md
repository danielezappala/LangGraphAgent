# LangGraph Agent

A full-stack application for managing LLM providers and running conversational AI workflows using LangGraph.

## Project Structure

```
├── backend/           # Python backend with FastAPI
├── frontend/          # Next.js frontend application  
├── docs/             # All project documentation
├── scripts/          # Development and utility scripts
├── data/             # Data files and performance results
├── config/           # Configuration files
└── .kiro/            # Kiro IDE configuration
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Development Setup

1. **Setup Environment**
   ```bash
   ./scripts/setup_env.sh
   ```

2. **Start Development**
   ```bash
   ./scripts/start-dev.sh
   ```

3. **Run Tests**
   ```bash
   python scripts/run_all_tests.py
   ```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System architecture overview
- **[Database Design](docs/unified_database_design.md)** - Database structure and design
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Database migration information
- **[Backend README](backend/README.md)** - Backend-specific documentation
- **[Frontend README](frontend/README.md)** - Frontend-specific documentation

## Features

- **LLM Provider Management** - Configure and manage multiple LLM providers
- **Conversational AI** - LangGraph-powered conversation workflows
- **Unified Database** - Single SQLite database for all data
- **Real-time Chat** - WebSocket-based real-time communication
- **Performance Monitoring** - Built-in performance tracking

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Conversation workflow management
- **SQLite** - Unified database system
- **WebSockets** - Real-time communication

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework

## Development

### Backend Development
```bash
cd backend
python run.py
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Testing
```bash
# All tests
python scripts/run_all_tests.py

# Backend tests only
python backend/run_tests.py

# Frontend tests only
cd frontend && npm test
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# LLM Provider (choose one)
LLM_PROVIDER=azure  # or openai

# Azure OpenAI (if using Azure)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment

# OpenAI (if using OpenAI)
OPENAI_API_KEY=your_key

# External APIs
TAVILY_API_KEY=your_tavily_key
NOTION_API_KEY=your_notion_key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.