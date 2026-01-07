# Popla Comet - Quick Start Guide

Get up and running with Popla Comet in minutes!

## 🚀 5-Minute Setup

### Option 1: Docker (Recommended for Quick Start)

The fastest way to get the backend running:

```bash
# 1. Clone and navigate
cd popla-comet

# 2. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start services
docker-compose up -d

# 4. Verify it's running
curl http://localhost:8000/health

# 5. Open API docs in browser
open http://localhost:8000/docs
```

### Option 2: Local Development (More Control)

#### Backend Setup (2 minutes)

```bash
# 1. Navigate to backend
cd popla-comet/backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp ../.env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run the server
python -m app.main

# Server is now running at http://localhost:8000
```

#### Android Setup (3 minutes)

```bash
# 1. Open Android Studio

# 2. Select "Open an Existing Project"

# 3. Navigate to popla-comet/android-app/

# 4. Wait for Gradle sync to complete

# 5. Click Run ▶️ or press Shift+F10
```

## 🧪 Verify Installation

### Backend Verification

```bash
# Check health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","service":"Popla Comet API","version":"0.1.0","openai_configured":true}

# Check API status
curl http://localhost:8000/api/v1/status

# Open interactive API docs
open http://localhost:8000/docs
```

### Android Verification

1. App should launch on emulator/device
2. You should see "Popla Comet" title
3. "Capture Image" button should be visible

## 📱 Using the Application

### Backend API Endpoints

#### Health Check
```bash
GET http://localhost:8000/health
```

#### API Status
```bash
GET http://localhost:8000/api/v1/status
```

#### Root Information
```bash
GET http://localhost:8000/
```

### Android App

Currently displays a welcome screen with:
- App title and description
- Camera capture button (UI only, functionality to be implemented)

## 🛠️ Common Commands

### Using Make (Recommended)

```bash
# View all available commands
make help

# Backend
make install-backend   # Install dependencies
make run-backend       # Run development server
make test-backend      # Run tests

# Android
make run-android       # Build and install app
make test-android      # Run tests

# Docker
make docker-up         # Start services
make docker-down       # Stop services
make docker-logs       # View logs

# Cleanup
make clean            # Remove build artifacts
```

### Manual Commands

#### Backend

```bash
# Run development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black .

# Lint code
ruff check .

# Type check
mypy app
```

#### Android

```bash
# Build debug APK
./gradlew assembleDebug

# Install on device
./gradlew installDebug

# Run tests
./gradlew test

# Run instrumentation tests
./gradlew connectedAndroidTest

# Lint
./gradlew lint

# Clean build
./gradlew clean
```

## 🔧 Configuration

### Backend Configuration

Edit `.env` file:

```bash
# Required
OPENAI_API_KEY=your_key_here

# Optional (defaults shown)
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
OPENAI_MODEL=gpt-4-vision-preview
MAX_UPLOAD_SIZE=10485760
```

### Android Configuration

Update backend URL in your code (for physical devices):

```kotlin
// In your network configuration (to be added)
const val BASE_URL = "http://your-computer-ip:8000"
```

For Android Emulator, use: `http://10.0.2.2:8000`

## 📊 Project Structure Quick Reference

```
popla-comet/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py   # API entry point
│   │   └── config.py # Configuration
│   └── tests/        # Backend tests
│
├── android-app/      # Android app
│   └── src/main/
│       └── kotlin/   # Kotlin source code
│
├── .env.example      # Environment template
├── docker-compose.yml
├── Makefile          # Development commands
└── README.md         # Full documentation
```

## 🎯 Next Steps

After completing the quick start:

1. **Explore the API**
   - Visit http://localhost:8000/docs
   - Try the interactive endpoints
   - Review the OpenAPI schema

2. **Customize the Backend**
   - Add new endpoints in `backend/app/main.py`
   - Create services in `backend/app/services/`
   - Add tests in `backend/tests/`

3. **Develop Android Features**
   - Implement camera capture
   - Add API service layer
   - Create ViewModels and screens

4. **Read the Documentation**
   - [Full README](./README.md)
   - [Architecture Guide](./ARCHITECTURE.md)
   - [Contributing Guide](./CONTRIBUTING.md)

## 🆘 Troubleshooting

### Backend Issues

**Port already in use**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Import errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

**OpenAI API errors**
```bash
# Verify your API key is set
echo $OPENAI_API_KEY
# Or check .env file
cat .env | grep OPENAI_API_KEY
```

### Android Issues

**Gradle sync failed**
- File → Invalidate Caches / Restart
- Delete `.gradle` and `build` folders
- Re-sync project

**Device not detected**
```bash
# Check connected devices
adb devices
# Restart adb
adb kill-server && adb start-server
```

**Build errors**
- Ensure JDK 17 is installed and configured
- Check Android SDK is properly installed
- Verify Gradle version compatibility

### Docker Issues

**Container won't start**
```bash
# Check logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

**Permission denied**
```bash
# On Linux, you might need to run with sudo
sudo docker-compose up -d
```

## 📚 Learn More

- [Backend API Documentation](http://localhost:8000/docs)
- [Full Project README](./README.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
- [Project Structure](./PROJECT_STRUCTURE.md)

## 🎉 You're Ready!

You now have:
- ✅ Backend API running
- ✅ Android development environment setup
- ✅ Understanding of basic commands
- ✅ Knowledge of project structure

Start building amazing features! 🚀

---

**Need Help?**
- Check the [full documentation](./README.md)
- Review [common issues](./CONTRIBUTING.md#troubleshooting)
- Open an issue on GitHub
