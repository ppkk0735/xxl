[app]

# (str) Title of your application
title = 消消乐最佳方案

# (str) Package name
package.name = matchfinder

# (str) Package domain (used for the APK ID)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (can be glob patterns)
source.include_exts = py,png,jpg,kv,atlas

# (list) Source files to exclude
source.exclude_exts = spec

# (list) List of requirements
requirements = python3,kivy,pillow

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 30

# (int) Minimum API required (Android 5.0)
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23b

# (str) Android SDK version to use
android.sdk = 30

# (bool) Use --private storage for APK data
android.private_storage = True

# (str) Android entry point, default is 'org.kivy.android.PythonActivity'
android.entrypoint = org.kivy.android.PythonActivity

# (bool) Add a meta-data to indicate using the GLESv3
# android.gles3 = False

# (str) Used to set the Android manifest's android:hardwareAccelerated attribute.
android.hardware_accelerated = True

# (str) Used to set the Android manifest's android:largeHeap attribute.
android.large_heap = False

# (bool) Add `android:usesCleartextTraffic="true"` to the manifest
# android.uses_cleartext_traffic = False

# (bool) Automatically accept SDK licenses
android.accept_sdk_license = True

# (str) Android architecture to build for (armeabi-v7a, arm64-v8a, x86, x86_64)
android.arch = armeabi-v7a, arm64-v8a

[buildozer]

# (str) Path to buildozer's global directory (where to store SDK, NDK, etc.)
# global_dir = ~/.buildozer

# (str) Path to the Android SDK directory (if not set, will be downloaded)
# android_sdk_dir =

# (str) Path to the Android NDK directory (if not set, will be downloaded)
# android_ndk_dir =

# (str) Path to the Android Ant directory (if not set, will be downloaded)
# android_ant_dir =

# (bool) If True, use the online Gradle build (recommended)
gradle = True

# (int) Number of parallel jobs to use for the build
# jobs = 2

# (bool) If True, will download the required dependencies automatically
autodownload = True
