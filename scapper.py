#!/usr/bin/env python3
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import termios
import tty
from typing import Optional

# Check arguments
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} video.mp4")
    sys.exit(1)

video_path = sys.argv[1]
current_frame = 0
saved_frames = []
all_frames = []

def get_duration():
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    try:
        duration = float(subprocess.check_output(cmd).decode().strip())
        return duration
    except:
        print("Error getting video duration")
        sys.exit(1)

def get_framerate():
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    try:
        framerate = subprocess.check_output(cmd).decode().strip()
        if not framerate:  # Handle empty output
            return 30.0  # Return default framerate
        try:
            num, den = map(float, framerate.split('/'))
            return num/den
        except ValueError:  # Handle non-fractional framerates
            return float(framerate)
    except:
        print("Error getting video framerate")
        return 30.0  # Return default framerate instead of exiting

def get_frame(timestamp):
    # Added -accurate_seek to prevent frame interpolation issues
    ffmpeg_cmd = ['ffmpeg', '-accurate_seek', '-ss', str(timestamp), '-i', video_path, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']
    try:
        return subprocess.check_output(ffmpeg_cmd, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error extracting frame")
        sys.exit(1)

def extract_all_frames():
    temp_dir = tempfile.mkdtemp()
    # Extract all frames without duplicates and ensure correct order
    ffmpeg_cmd = ['ffmpeg', '-i', video_path, '-vf', 'mpdecimate', '-vsync', '0', '-frame_pts', '1', os.path.join(temp_dir, 'frame_%d.png')]
    try:
        subprocess.run(ffmpeg_cmd, stderr=subprocess.DEVNULL)
        # Sort frames by their numerical index to maintain chronological order
        frames = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.png')],
                       key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[1]))
        return temp_dir, frames
    except subprocess.CalledProcessError:
        print("Error extracting frames")
        sys.exit(1)

def display_frame(frame_data):
    try:
        if isinstance(frame_data, bytes):
            viu_process = subprocess.Popen(['viu', '-'], stdin=subprocess.PIPE)
            viu_process.communicate(frame_data)
        else:
            subprocess.run(['viu', frame_data])
    except subprocess.CalledProcessError:
        print("Error displaying frame with viu")
        sys.exit(1)

def save_frame(frame_data, timestamp):
    if isinstance(frame_data, bytes):
        filename = f"frame_{timestamp:.3f}.png"
        with open(filename, 'wb') as f:
            f.write(frame_data)
    else:
        filename = f"frame_{timestamp:.3f}.png"
        shutil.copy2(frame_data, filename)
    saved_frames.append(filename)
    print(f"Saved {filename}")

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

print("\nControls:")
print("→: Forward 0.25s  ←: Back 0.25s")
print(".: Forward 1 frame  ,: Back 1 frame")
print("s: Save current frame")
print("q: Quit and save all marked frames\n")

duration = get_duration()

if duration <= 120:  # If video is 2 minutes or shorter
    try:
        print("Extracting all frames...")
        temp_dir, all_frames = extract_all_frames()
        total_frames = len(all_frames)
        framerate = get_framerate()

        while True:
            if 0 <= current_frame < total_frames:
                display_frame(all_frames[current_frame])
                print(f"\nCurrent frame: {current_frame+1}/{total_frames}")

                ch = getch()
                if ch == 'q':
                    break
                elif ch == 's':
                    save_frame(all_frames[current_frame], current_frame/total_frames * duration)
                elif ch == '.':
                    if current_frame < total_frames - 1:
                        current_frame += 1
                elif ch == ',':
                    current_frame = max(0, current_frame - 1)
                elif ch == '\x1b':
                    next1 = getch()
                    next2 = getch()
                    if next1 == '[':
                        frames_to_move = max(1, int(framerate * 0.25))
                        if next2 == 'C':  # Right arrow
                            current_frame = min(total_frames - 1, current_frame + frames_to_move)
                        elif next2 == 'D':  # Left arrow
                            current_frame = max(0, current_frame - frames_to_move)
            else:
                print("Frame index out of range")
                break
    finally:
        shutil.rmtree(temp_dir)  # Clean up temp directory even if error occurs
else:
    current_time = 0.0
    framerate = get_framerate()
    frame_duration = 1/framerate

    while True:
        frame = get_frame(current_time)
        display_frame(frame)
        print(f"\nCurrent timestamp: {current_time:.3f}s")

        ch = getch()
        if ch == 'q':
            break
        elif ch == 's':
            save_frame(frame, current_time)
        elif ch == '.':
            if current_time + frame_duration < duration:
                current_time += frame_duration
        elif ch == ',':
            current_time = max(0, current_time - frame_duration)
        elif ch == '\x1b':
            next1 = getch()
            next2 = getch()
            if next1 == '[':
                if next2 == 'C':  # Right arrow
                    if current_time + 0.25 < duration:
                        current_time += 0.25
                elif next2 == 'D':  # Left arrow
                    current_time = max(0, current_time - 0.25)

print(f"\nSaved {len(saved_frames)} frames:")
for frame in saved_frames:
    print(frame)
