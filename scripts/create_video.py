#!/usr/bin/env python3

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import shutil
import subprocess
import shutil
import sys
from os.path import dirname, abspath
from datetime import datetime
if __name__ == "__main__" and __package__ is None:
    sys.path.append(dirname(dirname(abspath(__file__))))
    from scripts.plot_cpu_total import plot_cpu_total
else:
    from .plot_cpu_total import plot_cpu_total

script_dir = os.path.dirname(os.path.abspath(__file__))
cpu_proc_logs_path = os.path.join(script_dir, '../data/cpu_proc_log')
cpu_total_log_path = os.path.join(script_dir, '../data/cpu-total.txt')
cpu_proc_logs_img_path = os.path.join(script_dir, '../data/cpu_proc_log_img')
stacked_folder_1_path = os.path.join(script_dir, '../data/cpu_stack_img_1')
cpu_total_img_path = os.path.join(script_dir, '../data/cpu-total-img')
output_video_path = os.path.join(script_dir, '../cpu.mp4')
cpu_proc_sampling_rate = 1

def create_output_folders(*folder_paths):
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

create_output_folders(
    # cpu_proc_logs_path,
    cpu_proc_logs_img_path,
    stacked_folder_1_path,
    cpu_total_img_path
)

def generate_proc_table_image(lines, timestamp, cpu_proc_logs_img_path):
    table_file_path = os.path.join(cpu_proc_logs_img_path, timestamp + '.png')
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)

    img = Image.new('RGB', (1280, 360), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    x = 10
    y = 10

    # Draw timestamp at the top of the image
    d.text((x, y), f"Time: {timestamp}", fill=(0, 0, 0), font=font)
    y += 30  # Increase y by a larger amount to leave space between the timestamp and the table
    
    for line in lines:
        d.text((x, y), line, fill=(0, 0, 0), font=font)
        y += 15

    img.save(table_file_path)
    return table_file_path
    
import inspect

def run_ffmpeg(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        result.check_returncode()
    except subprocess.CalledProcessError:
        print(f"Error occurred in function {inspect.stack()[1].function}.")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred in function {inspect.stack()[1].function}: {e}")
        exit(1)

def extract_timestamp(filename):
    return os.path.splitext(filename)[0]

def concatenate_total_to_proc(timestamp, total_dir, proc_dir, stacked_folder_1_path):    
    concat_proc_path = os.path.join(proc_dir, f'{timestamp}.png')
    concat_total_path = os.path.join(total_dir, f'{timestamp}.png')
    stacked_image_path = os.path.join(stacked_folder_1_path, f'{timestamp}.png')
    command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-hide_banner',
        '-i', concat_total_path,
        '-i', concat_proc_path,
        '-filter_complex', '[0:v]scale=1200:360[v0];[1:v]scale=1200:360[v1];[v0][v1]vstack',
        '-y', stacked_image_path
    ]
    run_ffmpeg(command)

    return stacked_image_path

def concatenate_images_to_video(input_folder, duration_per_image, output_video_path):  
    image_files = []
    for filename in os.listdir(input_folder):
        if filename.endswith('.png'):
            image_files.append(filename)
    
    sorted_image_files = sorted(image_files, key=lambda x: datetime.strptime(x.split('_')[0].split('.')[0], '%H-%M-%S'))
    concat_file_path = os.path.join('data/concat.txt')
    with open(concat_file_path, 'w') as file:
        for filename in sorted_image_files:
            file.write(f"file '{os.path.abspath(os.path.join(input_folder, filename))}'\nduration {duration_per_image}\n")

    command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-hide_banner',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file_path,
        '-framerate', '1',
        '-c:v', 'libx264',
        '-preset', 'ultrafast', 
        '-r', '1',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_video_path
    ]

    run_ffmpeg(command)
                
for filename in os.listdir(cpu_proc_logs_path):
    if filename.endswith('.txt'):
        # Load the text
        with open(os.path.join(cpu_proc_logs_path, filename), 'r') as file:
            lines = file.readlines()

        timestamp = os.path.splitext(filename)[0]
        cpu_total_plot_path = plot_cpu_total(timestamp, cpu_total_log_path, cpu_total_img_path)

        # # Generate the text image
        proc_table_image_filename = os.path.splitext(filename)[0] + '.png'
        generate_proc_table_image(lines, timestamp, cpu_proc_logs_img_path)

        # # Concatenate images
        concatenate_total_to_proc(timestamp, cpu_total_img_path, cpu_proc_logs_img_path, stacked_folder_1_path)
        
# concatenate images to video
concatenate_images_to_video(stacked_folder_1_path, cpu_proc_sampling_rate, output_video_path)