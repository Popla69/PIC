# Popla Comet Backend

FastAPI-based backend service for the Popla Comet mobile application.

## Features

- Computer vision and image analysis
- OpenAI GPT-4 Vision integration
- RESTful API with automatic documentation
- Health check and monitoring endpoints
- Docker support for easy deployment

## Requirements

- Python 3.9+
- OpenAI API key (for AI features)

## Installation

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```bash
cp ../.env.example .env
# Edit .env with your API keys
```

4. Run the development server:
```bash
python -m app.main
# Or using uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

Build and run with Docker:
```bash
docker build -t popla-comet-backend .
docker run -p 8000:8000 --env-file .env popla-comet-backend
```

Or use docker-compose from the root:
```bash
cd ..
docker-compose up backend
```

## API Documentation

Once running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Configuration management
│   └── services/        # Business logic and integrations
├── tests/               # Test suite
├── Dockerfile           # Container configuration
├── pyproject.toml       # Python project metadata and dependencies
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Development

### Testing

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy app
```

## Environment Variables

See `../.env.example` for all available configuration options.

Key variables:
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 Vision
- `DEBUG`: Enable debug mode (default: false)
- `PORT`: Server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
