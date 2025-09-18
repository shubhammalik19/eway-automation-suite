# Virtual Environment Setup Guide

## Creating Virtual Environment

This project requires a Python virtual environment. Follow these steps:

### Option 1: Using venv (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/MacOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Option 2: Using conda
```bash
# Create conda environment
conda create -n ewayauto python=3.11

# Activate environment
conda activate ewayauto

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Using pipenv
```bash
# Install pipenv if not installed
pip install pipenv

# Create virtual environment and install dependencies
pipenv install -r requirements.txt

# Activate environment
pipenv shell
```

## Environment Variables Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your actual configuration:
```bash
nano .env
# or
code .env
```

3. Update these critical values:
- `SECRET_KEY`: Generate a secure random string
- `EWAY_USERNAME`: Your EWay portal username
- `EWAY_PASSWORD`: Your EWay portal password
- `DEBUG`: Set to `false` for production

## Directory Structure Creation

The application will automatically create these directories when needed:
- `data/` - Database and data storage
- `logs/` - Application logs
- `app/static/screenshots/` - CAPTCHA and debug screenshots

## Browser Dependencies

Install Playwright browsers:
```bash
# After activating virtual environment
python -m playwright install

# Install system dependencies (Linux)
python -m playwright install-deps
```

## Running the Application

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/MacOS
# or
venv\Scripts\activate  # Windows

# Start the application
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Deactivating Virtual Environment

```bash
deactivate
```

## Troubleshooting

### Common Issues:

1. **ModuleNotFoundError**: Virtual environment not activated
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Playwright browsers not found**:
   ```bash
   python -m playwright install
   ```

3. **Permission denied on Linux**:
   ```bash
   sudo python -m playwright install-deps
   ```

4. **Port already in use**:
   ```bash
   # Change port in .env file or kill existing process
   lsof -ti:8000 | xargs kill -9
   ```

## Development Setup

For development with auto-reload:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Access the application at: http://127.0.0.1:8000