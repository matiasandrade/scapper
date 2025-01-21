# Scapper - Lossless Video Frame Capture Tool

A lightweight command-line tool for extracting high-quality PNG frames from video files, optimized for use with terminal image viewers that support the Kitty graphics protocol.

## Features

- Lossless PNG frame extraction from video files
- Real-time frame preview in terminal using kitty image protocol
- Frame-by-frame navigation and precise timestamp seeking
- Optimized handling of short videos (<2 minutes) by pre-extracting all frames
- Simple keyboard controls for frame navigation and capture

## Dependencies

- ffmpeg - For video processing and frame extraction
- viu - Terminal image viewer with kitty protocol support

## Installation

1. Ensure ffmpeg is installed on your system
2. Install viu: `cargo install viu`
3. Clone this repository and make the script executable:
