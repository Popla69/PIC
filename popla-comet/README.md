# Popla Comet

A modern full-stack computer vision and AI-powered image analysis platform consisting of a FastAPI backend and a native Android application.

## 🌟 Overview

Popla Comet combines cutting-edge AI capabilities with mobile-first design to provide powerful image analysis and computer vision features. The platform leverages OpenAI's GPT-4 Vision API, OpenCV for image processing, and modern Android development practices.

## 📁 Monorepo Structure

```
popla-comet/
├── backend/              # FastAPI backend service
│   ├── app/
│   │   ├── main.py      # FastAPI application entry point
│   │   ├── config.py    # Configuration management
│   │   └── services/    # Business logic and integrations
│   ├── tests/           # Backend tests
│   ├── Dockerfile       # Backend container configuration
│   ├── pyproject.toml   # Python dependencies and project metadata
│   └── requirements.txt # Python dependencies
│
├── android-app/         # Android mobile application
│   ├── src/main/
│   │   ├── kotlin/      # Kotlin source code
│   │   └── res/         # Android resources
│   ├── build.gradle.kts # Android build configuration
│   └── settings.gradle.kts
│
├── docs/                # Additional documentation
├── .env.example         # Environment variables template
├── docker-compose.yml   # Docker orchestration
├── ARCHITECTURE.md      # Architecture documentation
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- **Backend**:
  - Python 3.9 or higher
  - Docker (optional, for containerized deployment)
  - OpenAI API key

- **Android App**:
  - Android Studio Hedgehog (2023.1.1) or later
  - JDK 17+
  - Android SDK (API 26-34)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp ../.env.example .env
# Edit .env with your API keys
```

5. Run the development server:
```bash
python -m app.main
# Or: uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### Docker Deployment

From the root directory:

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Android App Setup

1. Open Android Studio

2. Select "Open an Existing Project"

3. Navigate to `popla-comet/android-app/`

4. Wait for Gradle sync to complete

5. Update the backend API URL if needed

6. Run the app on an emulator or physical device

## 🏗️ Architecture

The project follows modern best practices for both backend and mobile development:

### Backend Architecture

- **Framework**: FastAPI with async/await support
- **API Design**: RESTful with automatic OpenAPI documentation
- **Configuration**: Environment-based with pydantic-settings
- **Image Processing**: OpenCV and Pillow
- **AI Integration**: OpenAI GPT-4 Vision API
- **Deployment**: Docker with health checks

### Android Architecture

- **UI Framework**: Jetpack Compose with Material 3
- **Architecture Pattern**: Clean Architecture + MVVM
- **Language**: Kotlin with Coroutines
- **Networking**: Retrofit + OkHttp
- **Image Loading**: Coil
- **Dependency Injection**: Ready for Hilt/Koin integration

For detailed architecture information, see [ARCHITECTURE.md](./ARCHITECTURE.md)

## 📚 API Documentation

Once the backend is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Status**: http://localhost:8000/api/v1/status

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Android Tests

```bash
cd android-app
./gradlew test                    # Unit tests
./gradlew connectedAndroidTest    # Instrumentation tests
```

## 🛠️ Development

### Backend Development

- **Code Formatting**: `black .`
- **Linting**: `ruff check .`
- **Type Checking**: `mypy app`

### Android Development

- Follow Kotlin coding conventions
- Use Compose best practices
- Write tests for ViewModels and use cases
- Follow Material Design guidelines

## 📦 Dependencies

### Backend Core

- FastAPI - Modern web framework
- Uvicorn - ASGI server
- OpenAI - AI/ML capabilities
- OpenCV - Computer vision
- Pillow - Image processing
- Pydantic - Data validation

### Android Core

- Jetpack Compose - Declarative UI
- Material 3 - Design system
- Retrofit - HTTP client
- Coil - Image loading
- CameraX - Camera integration
- Kotlin Coroutines - Async operations

## 🔐 Security

- API keys stored in environment variables (never committed)
- CORS configuration for production
- Request size limits
- Image type validation
- HTTPS recommended for production
- ProGuard/R8 for Android release builds

## 🚢 Deployment

### Backend Deployment Options

1. **Docker** (Recommended):
   ```bash
   docker-compose up -d
   ```

2. **Cloud Platforms**:
   - AWS (ECS/Fargate, Lambda)
   - Google Cloud (Cloud Run, App Engine)
   - Azure (Container Instances, App Service)
   - Heroku, Railway, Render

3. **Traditional Hosting**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Android Deployment

1. Build release APK:
   ```bash
   ./gradlew assembleRelease
   ```

2. Sign and publish to Google Play Store

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

[MIT License](LICENSE)

## 🔗 Links

- [Backend Documentation](./backend/README.md)
- [Android App Documentation](./android-app/README.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs` endpoint

## 🗺️ Roadmap

- [ ] User authentication and authorization
- [ ] Image history and storage
- [ ] Batch image processing
- [ ] Real-time analysis streaming
- [ ] iOS app development
- [ ] Advanced ML model integration
- [ ] Analytics and monitoring
- [ ] Offline mode support
- [ ] Multi-language support
- [ ] Cloud storage integration

---

**Built with ❤️ by the Popla Team**
