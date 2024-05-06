import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from os import path
from datetime import datetime, date, time, timedelta
from matplotlib.ticker import FuncFormatter

def time_to_seconds(time):
    h, m, s = map(int, time.split('-'))
    return h*3600 + m*60 + s

def seconds_to_hm(x, pos):
    hours = int(x // 3600)
    minutes = int((x % 3600) // 60)
    return f'{hours:02d}:{minutes:02d}'

def plot_cpu_total(target_time, cpu_total_table_path, cpu_total_img_dir):
    
    columns = ['time', 'CPU', '%user', '%nice', '%system', '%iowait', '%steal', '%idle']
    df = pd.read_csv(cpu_total_table_path, sep='\s+', names=columns)

    df['%user'] = pd.to_numeric(df['%user'], errors='coerce')
    df['%system'] = pd.to_numeric(df['%system'], errors='coerce')
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
    df['time'] = df['time'].apply(lambda t: t.hour*3600 + t.minute*60 + t.second)

    plt.figure(figsize=(12.8, 3.6))

    target_time_seconds = time_to_seconds(target_time)
    # Add a vertical line representing the current time
    plt.axvline(x=target_time_seconds, color='r', linestyle='--')
    
    # Format the x-axis labels as H:M
    ax = plt.gca()  
    formatter = FuncFormatter(seconds_to_hm) 
    ax.xaxis.set_major_formatter(formatter)  

    plt.plot(df['time'], df['%system'], label='%system')
    plt.plot(df['time'], df['%user'], label='%user')
    plt.xlabel('Time')
    plt.ylabel('CPU usage (%)')
    plt.ylim(0, 100) 
    plt.legend(fontsize='large')
    plt.tight_layout()
    filename = f'{target_time}.png'
    output_path = path.join(cpu_total_img_dir, filename)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close() 
    

# plot_cpu('17-49-00', '../data/cpu-total.txt', '../data/cpu-total-img')