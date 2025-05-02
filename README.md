# HackUPC-2025 Backend

A FastAPI backend for the HackUPC 2025 project.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Project Structure

```
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── app/
    ├── models/          # Pydantic models
    ├── routers/         # API endpoints
    ├── services/        # Business logic
    └── db/              # Database connections and models
``` 