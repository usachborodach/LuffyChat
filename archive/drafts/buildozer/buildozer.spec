[app]

title = LuffyChat
package.name = luffychat
package.domain = org.luffy
version = 1.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
main.py = mobile_app.py

# Минимальные требования для теста
requirements = python3,kivy,requests

android.accept_sdk_license = true
android.archs = arm64-v8a
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.permissions = INTERNET,ACCESS_NETWORK_STATE

orientation = portrait
fullscreen = 0

log_level = 2
