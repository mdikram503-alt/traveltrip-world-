[app]
title = Traveler
package.name = traveler
package.domain = world.traveltrip
source.dir = .
source.include_exts = py,kv,png,jpg,json
version = 1.0.0
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
ios.kivy_ios_url = https://github.com/kivy/kivy-ios

[buildozer]
log_level = 2
warn_on_root = 1
