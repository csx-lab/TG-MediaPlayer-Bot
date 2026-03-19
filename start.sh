#!/bin/bash

# 1. Download FFmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz -o ffmpeg.tar.xz
tar -xJf ffmpeg.tar.xz
mv ffmpeg-*/ffmpeg ffmpeg-*/ffprobe /usr/local/bin/
chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# 2. Start bot
python main.py
