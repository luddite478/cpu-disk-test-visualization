#!/usr/bin/env python3

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import shutil
import os
import subprocess
import shutil
from datetime import datetime, timedelta

# Specify the folder paths
cpu_logs_path = 'data/cpu_processes_log'
output_folder_path = 'data/cpu_logs_img'
stacked_folder_1_path = 'data/cpu_stack_img_1'
timestamp_folder_path = 'data/timestamp_img'
stacked_folder_2_path = 'data/cpu_stack_img_2'
cpu_total_plot_path = 'data/cpu-total.png'
output_video_path = 'cpu.mp4'
cpu_proc_sampling_rate = 1

def create_output_folders(output_folder_path, stacked_folder_1_path, timestamp_folder_path):
    if os.path.exists(output_folder_path):
        shutil.rmtree(output_folder_path)

    if os.path.exists(stacked_folder_1_path):
        shutil.rmtree(stacked_folder_1_path)

    if os.path.exists(timestamp_folder_path):
        shutil.rmtree(timestamp_folder_path)

    if os.path.exists(stacked_folder_2_path):
        shutil.rmtree(stacked_folder_2_path)

    if os.path.exists(stacked_folder_2_path):
        shutil.rmtree(stacked_folder_2_path)

    os.makedirs(output_folder_path)
    os.makedirs(stacked_folder_1_path)
    os.makedirs(timestamp_folder_path)
    os.makedirs(stacked_folder_2_path)

def generate_proc_table_image(lines, output_image_path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)

    img = Image.new('RGB', (500, 300), color=(73, 109, 137))
    d = ImageDraw.Draw(img)

    x = 10
    y = 10

    # Draw each line separately
    for line in lines:
        d.text((x, y), line, fill=(255, 255, 0), font=font)
        y += 15  # Move to the next line. Adjust the value as needed.

    img = img.resize((640, 480))

    img.save(output_image_path)

def concatenate_horizontal(img1, img2, output_image_path):
    command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-hide_banner',
        '-i', img1,
        '-i', img2,
        '-filter_complex', 'hstack',
        '-y', output_image_path
    ]
    try:
        subprocess.call(command)
    except Exception as e:
        print(f"Error occurred while concatenating images horizontally: {e}")

def concatenate_vertical(img1, img2, output_image_path):
    command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-hide_banner',
        '-i', img1,
        '-i', img2,
        '-filter_complex', 'vstack',
        '-y', output_image_path
    ]
    try:
        subprocess.call(command)
    except Exception as e:
        print(f"Error occurred while concatenating images vertically: {e}")

def generate_timestamp_image(timestamp, output_image_path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)

    timestamp_img = Image.new('RGB', (1280, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(timestamp_img)
    d.text((500, 20), timestamp, fill=(255, 255, 0), font=font)

    timestamp_img.save(output_image_path)

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

    try:
        subprocess.call(command)
    except Exception as e:
        print(f"Error occurred while merging images to the video: {e}")

    # os.remove(concat_file_path)

create_output_folders(output_folder_path, stacked_folder_1_path, timestamp_folder_path)

# Iterate over the .txt files in the folder
for filename in os.listdir(cpu_logs_path):
    if filename.endswith('.txt'):
        # Load the text
        with open(os.path.join(cpu_logs_path, filename), 'r') as file:
            lines = file.readlines()

        # Generate the text image
        image_filename = os.path.splitext(filename)[0] + '.png'
        image_stack_1_path = os.path.join(output_folder_path, image_filename)
        generate_proc_table_image(lines, image_stack_1_path)

        # Concatenate images
        stacked_image_path = os.path.join(stacked_folder_1_path, image_filename)
        concatenate_horizontal(cpu_total_plot_path, image_stack_1_path, stacked_image_path)
        
        # Generate timestamp image
        timestamp = os.path.splitext(filename)[0].replace('top-cpu-', '')
        timestamp_image_path = os.path.join(timestamp_folder_path, image_filename)
        generate_timestamp_image(timestamp, timestamp_image_path)

        stacked_imge_2_path = os.path.join(stacked_folder_2_path, timestamp + '_stack.png')
        concatenate_vertical(stacked_image_path, timestamp_image_path, stacked_imge_2_path)

        # start = 44,412
        # end = 619,412 


# concatenate images to video
concatenate_images_to_video(stacked_folder_2_path, cpu_proc_sampling_rate, output_video_path)