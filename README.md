# Smart Barn Monitor 🐄

A modern desktop application built with PyQt6, OpenCV, and PyAV to monitor RTSP streams coming from IP cameras with built-in ONVIF PTZ controls and real-time audio analysis.

## Features
- **Live Video Streaming:** Low-latency RTSP playback with error recovery.
- **Audio Monitoring (Moo Detection):** Smart continuous noise and threshold analysis.
- **Full ONVIF PTZ Support:** Smoothly control Pan, Tilt, Zoom, and save custom Presets without leaving the app.
- **Telegram Notifications:** Get real-time alerts pushed entirely asynchronously to your Telegram mobile app without freezing the desktop UI.

## Telegram Integration 📱
Smart Barn Monitor allows you to get mobile push notifications directly via a Telegram Bot. 

1. **Create a Bot**
   - Open Telegram and search for `@BotFather`.
   - Send `/newbot`, and follow the steps to create a bot.
   - It will provide you with a **Bot Token** (e.g. `123456789:ABCDEF...`).

2. **Get Your Chat ID**
   - Search for `@userinfobot` or similar bots on Telegram to find out your numeric `Chat ID`.
   - You can also add your new bot to a group, and fetch the Group Chat ID to broadcast alarms to everyone.

3. **Configure the App**
   - Open Smart Barn Monitor.
   - Click the blue **Telegram** button near the top right.
   - Paste the Token and Chat ID.
   - Hit **"Bağlantıyı Test Et"**; if successful, you will instantly receive a message in Telegram!

## 🔐 Security Notice Regarding Config
The data you enter inside the application (IP Camera passwords, Telegram Bot Tokens, etc.) is saved to a local file called `config.json`. 

> **IMPORTANT**: We have configured `.gitignore` to specifically reject `config.json`. Do **NOT** manually commit or push this file to GitHub or any public version control system. Your credentials must stay local!

## Installation & Running
```bash
pip install -r requirements.txt
python src/main.py
```
