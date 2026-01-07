# Changelog

All notable changes to the Popla Comet project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Image analysis endpoints
- OpenAI GPT-4 Vision integration
- Camera capture functionality
- Image gallery selection
- User authentication
- Result history and storage
- Batch processing
- Real-time analysis streaming

## [0.1.0] - 2024-01-07

### Added

#### Backend
- Initial FastAPI application structure
- Health check endpoint (`/health`)
- API status endpoint (`/api/v1/status`)
- Configuration management with Pydantic Settings
- Environment-based configuration
- Docker support with health checks
- CORS middleware configuration
- Automatic API documentation (OpenAPI/Swagger)
- Python project structure with pyproject.toml
- Development dependencies setup
- Basic test structure with pytest
- Code quality tools (black, ruff, mypy)

#### Android
- Initial Android project with Kotlin
- Jetpack Compose UI framework
- Material 3 design system
- MainActivity with basic UI
- Theme configuration (colors, typography)
- Resource files (strings, colors)
- Gradle build configuration
- Dependencies setup:
  - Jetpack Compose
  - Retrofit for networking
  - Coil for image loading
  - Kotlin Coroutines
  - CameraX
  - Navigation
- ProGuard rules for release builds
- Android manifest with permissions

#### Infrastructure
- Monorepo structure at `popla-comet/`
- Docker Compose configuration
- Environment variables template (`.env.example`)
- Comprehensive documentation:
  - README.md with project overview
  - ARCHITECTURE.md with design details
  - PROJECT_STRUCTURE.md with file organization
  - CONTRIBUTING.md with guidelines
- Makefile for common development tasks
- .gitignore for both Python and Android
- MIT License

#### Documentation
- Complete project structure documentation
- Architecture diagrams and explanations
- API documentation setup
- Development workflow guidelines
- Code style guidelines
- Testing guidelines
- Contribution guidelines

### Technical Details

- **Backend Stack**: Python 3.9+, FastAPI, Uvicorn, OpenAI, OpenCV, Pillow
- **Android Stack**: Kotlin 1.9.21, Compose, Material 3, Retrofit, Coil
- **Build Tools**: Gradle 8.4, setuptools, Docker
- **Testing**: pytest, JUnit, Compose UI tests
- **Code Quality**: black, ruff, mypy, ktlint

### Development Setup

- Virtual environment setup for backend
- Docker containerization
- Gradle wrapper for Android
- Development and production configurations

---

## Release Types

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

---

[Unreleased]: https://github.com/popla/comet/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/popla/comet/releases/tag/v0.1.0
