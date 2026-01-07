# Popla Comet - Project Structure

This document provides a complete overview of the Popla Comet monorepo structure.

## 📁 Complete Directory Structure

```
popla-comet/
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── ARCHITECTURE.md                 # Architecture documentation
├── PROJECT_STRUCTURE.md           # This file
├── README.md                      # Main project documentation
├── docker-compose.yml             # Docker orchestration configuration
│
├── backend/                       # Python FastAPI Backend
│   ├── .dockerignore             # Docker ignore rules
│   ├── Dockerfile                # Backend container configuration
│   ├── README.md                 # Backend documentation
│   ├── pyproject.toml            # Python project configuration
│   ├── requirements.txt          # Python dependencies
│   │
│   ├── app/                      # Application source code
│   │   ├── __init__.py          # Package initialization
│   │   ├── config.py            # Configuration management
│   │   ├── main.py              # FastAPI application entry point
│   │   │
│   │   └── services/            # Service layer
│   │       └── __init__.py      # Services package init
│   │
│   └── tests/                   # Backend tests
│       └── .gitkeep
│
├── android-app/                  # Android Application
│   ├── README.md                # Android app documentation
│   ├── build.gradle.kts         # Application build configuration
│   ├── gradle.properties        # Gradle properties
│   ├── proguard-rules.pro       # ProGuard/R8 rules
│   ├── settings.gradle.kts      # Gradle settings
│   │
│   ├── gradle/                  # Gradle wrapper
│   │   └── wrapper/
│   │       └── gradle-wrapper.properties
│   │
│   └── src/main/               # Main source set
│       ├── AndroidManifest.xml # App manifest
│       │
│       ├── kotlin/             # Kotlin source code
│       │   └── com/popla/comet/
│       │       ├── MainActivity.kt
│       │       │
│       │       └── ui/theme/   # UI Theme
│       │           ├── Color.kt
│       │           ├── Theme.kt
│       │           └── Type.kt
│       │
│       └── res/                # Android resources
│           ├── drawable/       # Drawable resources
│           ├── layout/         # XML layouts (if needed)
│           ├── mipmap-hdpi/    # App icons (hdpi)
│           ├── mipmap-mdpi/    # App icons (mdpi)
│           ├── mipmap-xhdpi/   # App icons (xhdpi)
│           ├── mipmap-xxhdpi/  # App icons (xxhdpi)
│           ├── mipmap-xxxhdpi/ # App icons (xxxhdpi)
│           │
│           └── values/         # Value resources
│               ├── colors.xml  # Color definitions
│               ├── strings.xml # String resources
│               └── themes.xml  # Theme definitions
│
└── docs/                       # Additional documentation
    └── .gitkeep
```

## 📦 Key Files Overview

### Root Level

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables (API keys, config) |
| `.gitignore` | Git ignore patterns for Python, Android, and general files |
| `README.md` | Main project documentation with quick start guide |
| `ARCHITECTURE.md` | Detailed architecture and design decisions |
| `docker-compose.yml` | Docker services orchestration for local development |

### Backend Files

| File | Purpose |
|------|---------|
| `backend/pyproject.toml` | Python project metadata, dependencies, and tool configuration |
| `backend/requirements.txt` | Python package dependencies |
| `backend/Dockerfile` | Container image definition for backend |
| `backend/app/main.py` | FastAPI application with routes and middleware |
| `backend/app/config.py` | Pydantic-based configuration management |

### Android Files

| File | Purpose |
|------|---------|
| `android-app/build.gradle.kts` | Gradle build configuration with dependencies |
| `android-app/settings.gradle.kts` | Gradle project settings |
| `android-app/gradle.properties` | Gradle JVM and build properties |
| `android-app/proguard-rules.pro` | Code obfuscation and optimization rules |
| `android-app/src/main/AndroidManifest.xml` | App permissions, activities, and metadata |
| `android-app/src/main/kotlin/.../MainActivity.kt` | Main activity with Compose UI |

## 🛠️ Technology Stack Summary

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Server**: Uvicorn
- **AI/ML**: OpenAI GPT-4 Vision
- **Image Processing**: OpenCV, Pillow
- **Config**: Pydantic Settings
- **Container**: Docker

### Android
- **Language**: Kotlin 1.9.21
- **UI**: Jetpack Compose + Material 3
- **Architecture**: MVVM + Clean Architecture
- **Networking**: Retrofit + OkHttp
- **Image Loading**: Coil
- **Async**: Kotlin Coroutines
- **Build**: Gradle 8.4

## 🚀 Getting Started

### Backend Quick Start
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your API keys
python -m app.main
```

### Android Quick Start
```bash
cd android-app
# Open in Android Studio
# Or use command line:
./gradlew assembleDebug
./gradlew installDebug
```

### Docker Quick Start
```bash
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```

## 📋 Development Checklist

### Backend Development
- [x] Project structure created
- [x] FastAPI application initialized
- [x] Configuration management setup
- [x] Health check endpoints
- [x] Docker configuration
- [ ] Add image analysis endpoints
- [ ] Implement OpenAI integration
- [ ] Add OpenCV processing
- [ ] Write unit tests
- [ ] Add logging and monitoring

### Android Development
- [x] Project structure created
- [x] MainActivity with Compose
- [x] Material 3 theme setup
- [x] Resource files created
- [x] Build configuration
- [ ] Implement camera capture
- [ ] Add image selection
- [ ] Create API service layer
- [ ] Implement ViewModels
- [ ] Add navigation
- [ ] Write unit tests

## 🔄 Planned Additions

### Services (Backend)
```
backend/app/services/
├── image_service.py      # Image validation and processing
├── ai_service.py         # OpenAI API integration
├── analysis_service.py   # Computer vision operations
└── storage_service.py    # File storage handling
```

### Data Layer (Android)
```
android-app/src/main/kotlin/com/popla/comet/
├── data/
│   ├── api/             # Retrofit services
│   ├── model/           # Data models
│   └── repository/      # Repository implementations
├── domain/
│   ├── model/           # Domain models
│   ├── repository/      # Repository interfaces
│   └── usecase/         # Business use cases
└── presentation/
    ├── analysis/        # Analysis screen
    ├── capture/         # Camera capture screen
    └── result/          # Results display screen
```

## 📝 Notes

- All Python dependencies use version constraints for stability
- Android app targets SDK 34 (Android 14) with minimum SDK 26
- Docker configuration includes health checks and volume mounts
- Environment variables managed through `.env` file (not committed)
- Both backend and Android follow clean architecture principles
- Git ignores build artifacts, caches, and sensitive files

## 🔗 Related Documentation

- [Main README](./README.md) - Project overview and setup
- [Architecture Guide](./ARCHITECTURE.md) - Detailed architecture
- [Backend README](./backend/README.md) - Backend specific docs
- [Android README](./android-app/README.md) - Android specific docs

## 📞 Support

For questions or issues:
1. Check the relevant README files
2. Review the ARCHITECTURE.md
3. Check API documentation at http://localhost:8000/docs (when backend is running)
4. Open an issue on the project repository

---

**Last Updated**: $(date)
**Version**: 0.1.0
**Status**: Initial Setup Complete ✅
