# Popla Comet Android App

Modern Android application built with Kotlin and Jetpack Compose for computer vision and AI-powered image analysis.

## Features

- Camera integration for image capture
- Image selection from gallery
- Real-time image analysis via backend API
- Modern Material 3 design
- Jetpack Compose UI
- Kotlin Coroutines for async operations

## Requirements

- Android Studio Hedgehog (2023.1.1) or later
- Minimum SDK: 26 (Android 8.0)
- Target SDK: 34 (Android 14)
- Kotlin 1.9.21+
- Gradle 8.2+

## Setup

1. Open Android Studio
2. Select "Open an Existing Project"
3. Navigate to `popla-comet/android-app/`
4. Wait for Gradle sync to complete

## Configuration

Update the backend API URL in your code:
```kotlin
// In your network configuration
const val BASE_URL = "http://10.0.2.2:8000"  // For Android Emulator
// const val BASE_URL = "http://your-backend-url:8000"  // For physical device
```

## Building

### Debug Build
```bash
./gradlew assembleDebug
```

### Release Build
```bash
./gradlew assembleRelease
```

## Running

1. Connect an Android device or start an emulator
2. Click "Run" in Android Studio or use:
```bash
./gradlew installDebug
```

## Project Structure

```
android-app/
├── src/main/
│   ├── kotlin/com/popla/comet/
│   │   ├── MainActivity.kt          # Main activity
│   │   ├── ui/theme/                # Theme configuration
│   │   │   ├── Color.kt
│   │   │   ├── Theme.kt
│   │   │   └── Type.kt
│   │   ├── data/                    # Data layer (to be added)
│   │   ├── domain/                  # Domain layer (to be added)
│   │   └── presentation/            # UI layer (to be added)
│   ├── res/                         # Resources
│   │   ├── values/
│   │   │   ├── strings.xml
│   │   │   ├── colors.xml
│   │   │   └── themes.xml
│   │   ├── layout/
│   │   ├── drawable/
│   │   └── mipmap-*/
│   └── AndroidManifest.xml
├── build.gradle.kts                 # App-level build configuration
├── proguard-rules.pro               # ProGuard rules
└── README.md                        # This file
```

## Architecture

The app follows Clean Architecture principles with MVVM pattern:

- **Presentation Layer**: Jetpack Compose UI + ViewModels
- **Domain Layer**: Use cases and business logic
- **Data Layer**: Repository pattern with Retrofit for API calls

## Key Dependencies

- **Jetpack Compose**: Modern declarative UI toolkit
- **Material 3**: Latest Material Design components
- **Retrofit**: Type-safe HTTP client
- **Coil**: Image loading library
- **Kotlin Coroutines**: Asynchronous programming
- **CameraX**: Camera integration
- **Navigation**: Jetpack Navigation Compose

## Testing

Run unit tests:
```bash
./gradlew test
```

Run instrumentation tests:
```bash
./gradlew connectedAndroidTest
```

## Permissions

The app requires the following permissions:
- `CAMERA`: For capturing images
- `READ_MEDIA_IMAGES`: For selecting images from gallery (Android 13+)
- `READ_EXTERNAL_STORAGE`: For selecting images from gallery (older versions)
- `INTERNET`: For API communication

## Next Steps

- [ ] Implement camera capture functionality
- [ ] Add image gallery selection
- [ ] Implement API service layer
- [ ] Add loading states and error handling
- [ ] Implement result display screen
- [ ] Add image upload to backend
- [ ] Implement caching strategy
- [ ] Add offline support
- [ ] Implement authentication
- [ ] Add analytics

## Development Guidelines

- Follow Kotlin coding conventions
- Use Compose best practices
- Write unit tests for ViewModels and use cases
- Use coroutines for async operations
- Follow Material Design guidelines
- Keep composables small and focused
- Use state hoisting appropriately
