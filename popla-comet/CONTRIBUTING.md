# Contributing to Popla Comet

Thank you for your interest in contributing to Popla Comet! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.9+ (for backend)
- Node.js and npm (for tooling)
- Android Studio Hedgehog or later (for Android development)
- Docker and Docker Compose (optional, for containerized development)
- Git

### Setting Up Your Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/popla-comet.git
   cd popla-comet
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install dev dependencies
   ```

3. **Android Setup**
   - Open Android Studio
   - Open the `android-app` directory
   - Wait for Gradle sync
   - Configure an emulator or connect a device

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## 📝 Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow the style guides (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Android tests
   cd android-app
   ./gradlew test
   ./gradlew connectedAndroidTest
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add image upload endpoint
fix: resolve null pointer exception in MainActivity
docs: update API documentation
test: add unit tests for image service
```

## 🎨 Code Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use `black` for formatting: `black .`
- Use `ruff` for linting: `ruff check .`
- Use `mypy` for type checking: `mypy app`

Example:
```python
from typing import Optional

async def process_image(
    image_data: bytes,
    analysis_type: str,
    options: Optional[dict] = None
) -> dict:
    """Process an image with the specified analysis type.
    
    Args:
        image_data: Raw image bytes
        analysis_type: Type of analysis to perform
        options: Optional processing parameters
        
    Returns:
        Dictionary containing analysis results
    """
    # Implementation
    pass
```

### Kotlin (Android)

- Follow [Kotlin Coding Conventions](https://kotlinlang.org/docs/coding-conventions.html)
- Maximum line length: 120 characters
- Use meaningful variable names
- Prefer `val` over `var`
- Use Compose best practices

Example:
```kotlin
@Composable
fun ImageAnalysisScreen(
    viewModel: AnalysisViewModel = viewModel(),
    onNavigateBack: () -> Unit
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Image Analysis") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        AnalysisContent(
            state = state,
            modifier = Modifier.padding(paddingValues)
        )
    }
}
```

## 🧪 Testing Guidelines

### Backend Testing

- Write unit tests for all services
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Use pytest fixtures for test data
- Mock external API calls

Example:
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Android Testing

- Write unit tests for ViewModels and use cases
- Write UI tests for critical user flows
- Test both success and error scenarios
- Use appropriate test doubles (mocks, fakes)

Example:
```kotlin
@Test
fun `viewModel loads analysis results successfully`() = runTest {
    val mockRepository = MockAnalysisRepository()
    val viewModel = AnalysisViewModel(mockRepository)
    
    viewModel.loadAnalysis("test-id")
    
    val state = viewModel.state.value
    assertTrue(state is AnalysisState.Success)
    assertEquals("test-id", (state as AnalysisState.Success).data.id)
}
```

## 📚 Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for architectural changes
- Add inline comments for complex logic
- Update API documentation (OpenAPI)
- Add JSDoc/KDoc comments for public APIs

## 🔍 Pull Request Process

1. **Before Submitting**
   - Ensure all tests pass
   - Run linters and formatters
   - Update documentation
   - Rebase on latest `develop` branch

2. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing performed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests pass locally
   ```

3. **Review Process**
   - At least one approval required
   - All CI checks must pass
   - Address review comments
   - Maintain discussion in PR

## 🐛 Reporting Bugs

### Before Reporting

- Check existing issues
- Test on latest version
- Gather reproduction steps

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment**
- OS: [e.g., macOS 13.0]
- Python version: [e.g., 3.11]
- Android version: [e.g., Android 14]
- App version: [e.g., 0.1.0]

**Additional context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Any other relevant information
```

## 🔐 Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Report security issues privately
- Follow OWASP guidelines

## 📞 Getting Help

- Check documentation first
- Search existing issues
- Ask in discussions
- Join our community chat

## 🎯 Development Tips

### Backend Tips

- Use `uvicorn app.main:app --reload` for hot reload
- Check logs with `docker-compose logs -f backend`
- Use `pytest -v` for verbose test output
- Profile slow endpoints with `cProfile`

### Android Tips

- Use Android Studio's profiler for performance
- Enable strict mode during development
- Use Compose preview for quick UI iteration
- Check Logcat for debugging

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project website

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to Popla Comet! 🚀
