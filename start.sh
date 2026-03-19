#!/bin/bash

# FFmpeg download
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz -o ffmpeg.tar.xz
tar -xJf ffmpeg.tar.xz
mv ffmpeg-*/ffmpeg ffmpeg-*/ffprobe /usr/local/bin/
chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Optional: verify PyTgCalls version
python -c "import pytgcalls; print('PyTgCalls version:', pytgcalls.__version__)"

# Start bot
python main.py
