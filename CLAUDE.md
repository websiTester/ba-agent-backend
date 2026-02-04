# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BA-Agent** is a Business Analysis Agent system built with FastAPI, LangGraph, and Google Gemini AI. The system uses a **dynamic multi-agent orchestration architecture** where agents are configured in MongoDB and assembled at runtime into LangGraph workflows.

**Tech Stack**: Python 3.12, FastAPI, LangGraph, LangChain, Google Gemini AI (gemini-2.5-flash), MongoDB, ChromaDB

## Development Commands

### Running the Application

```bash
# Local development with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Docker build
docker build -t ba-agent-backend .

# Docker run
docker run -p 8000:8000 --env-file .env ba-agent-backend
```

### Environment Setup

Create a `.env` file with:
```
MONGODB_URI=mongodb://localhost:27017/mastraDB2
GOOGLE_API_KEY=your_api_key_here
```

## Architecture Overview

### Multi-Agent Graph System

The system dynamically builds LangGraph workflows from MongoDB configuration:

1. **Graph Creation** (`graphs/ba_dynamic_graph.py`):
   - `create_new_graph_from_db()` reads tools from MongoDB
   - Each tool becomes a node in the LangGraph
   - A supervisor node orchestrates agent routing
   - Uses singleton pattern with `_GLOBAL_BA_GRAPH` for caching

2. **Supervisor Node** (`graph_nodes/create_node_from_db.py`):
   - Manages conversation flow between agents
   - Uses dynamic Pydantic models with StrEnum for routing
   - Routes to agents or "FINISH" to end workflow
   - Handles retry logic with API key rotation

3. **Agent Nodes** (`graph_nodes/create_agent_node.py`):
   - Each agent is a specialized LangChain agent
   - Configured with system prompts from MongoDB
   - Returns to supervisor after completion
   - Uses Command pattern for state updates

### State Management

- **State** (`models/state.py`): Extends LangGraph's `MessagesState` with `next` field
- **Memory**: Uses `MemorySaver` checkpointer for conversation persistence
- **Thread ID**: Configured in graph invocation config

### Database-Driven Configuration

**MongoDB Collections**:
- `tools`: Agent configurations (toolName, toolDescription, fields, prompts)
- `agents`: Special agents like "Orchestration_Agent"
- `apikeys`: Rotating API keys for Google Gemini
- `ai_responses`: Stored agent outputs by phase_id

**Key Pattern**: Configuration lives in database, not code. To add a new agent:
1. Insert document in `tools` collection
2. Call `/tools_management/refresh_agent` endpoint
3. Graph rebuilds automatically with new agent

### API Key Management

- **Singleton Cache** (`graph_nodes/apikey_helper.py`): API keys cached in `_cached_api_key`
- **Rotation**: On Google API errors (ResourceExhausted), calls `refresh_api_key()` to fetch next key from DB
- **LLM Factory**: `get_llm(model_name)` returns configured ChatGoogleGenerativeAI instance

### Response Processing

- **Structured Output** (`utils/response_processor.py`):
  - Agents return JSON with `agent_source` and `data` fields
  - Supports CSV/PSV parsing into arrays
  - Uses `json_repair` for malformed JSON
  - Deduplicates by `agent_source`
  - Saves to MongoDB with `phaseId`

## Key File Locations

- **Entry Point**: `main.py` - FastAPI app with CORS and routers
- **Graph Creation**: `graphs/ba_dynamic_graph.py` - Dynamic graph assembly and retry logic
- **Node Factory**: `graph_nodes/create_node_from_db.py` - Supervisor and agent node creation
- **Agent Builder**: `graph_nodes/create_agent_node.py` - Individual agent nodes
- **Tool Factory**: `tools/create_tool_from_db.py` - Dynamic tool creation from DB
- **MongoDB CRUD**: `mongodb/actions/` - Database operations
- **API Endpoints**: `routers/agent_response.py` - Main agent invocation endpoint

## Critical Patterns

### Dynamic Tool Creation

Tools in MongoDB have a nested structure:
- Outer tool: Used by orchestrating agent (e.g., "Discovery_Requirements")
- Inner tool: Used by the agent itself (e.g., "discovery_tool")
- The pattern uses `StructuredTool.from_function` with partial application to bind agent executors

### Error Handling and Retries

Graph invocation (`get_ba_graph_response` in `ba_dynamic_graph.py`):
1. Catches Google API errors (ResourceExhausted, ServerError)
2. Exponential backoff with max 30s wait
3. Refreshes API key and graph on retry
4. Returns all AI messages after last HumanMessage

### Message Extraction

`getAllResponse()` function:
- Finds last HumanMessage in history
- Returns all AI messages after that point
- Allows multi-turn agent conversations

## Common Development Tasks

### Adding a New Agent Type

1. Insert into MongoDB `tools` collection with required fields:
   - `toolName`, `toolDescription`, `agentToolName`, `agentToolDescription`
   - `instruction`: System prompt for the agent
   - `field`: Input schema (user_input, phase_id, etc.)

2. Refresh graph: `PUT /tools_management/refresh_agent`

### Debugging Agent Responses

Check console output for:
- `State supervisor_node`: Shows messages passed to supervisor
- `Response supervisor_node`: Shows routing decision
- `below my goto`: Shows next agent selected

### Updating Agent Instructions

Instructions stored in MongoDB `tools.instruction` field. Update DB and refresh graph.

## Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase` (e.g., `State`, `Router`)
- **Files**: `snake_case.py`
- **Environment Variables**: `SCREAMING_SNAKE_CASE`

## Important Notes

- **Graph is Cached**: Call `refresh_ba_graph()` after DB changes
- **API Keys Rotate**: System automatically tries next key on quota errors
- **Supervisor is Required**: All agent nodes return to supervisor via `Command(goto="supervisor")`
- **Thread ID = 1**: Currently hardcoded; future work needed for multi-user support
- **Vietnamese Comments**: Codebase contains Vietnamese comments and variable names
