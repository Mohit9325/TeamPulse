[app]
title = TeamPulse
package.name = teampulse
package.domain = org.teampulse
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,qml,json,db
version = 0.1
requirements = python3==3.11,pyside6,firebase-admin,sqlite3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
