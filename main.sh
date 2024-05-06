#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y fio sysstat ffmpeg python3-pip
pip install Pillow datetime pandas matplotlib

MONITORING_DURATION="1800"
DISK_LOAD_DURATION="1800" # set this lower to see the CPU usage without disk load
TOTAL_CPU_SAMPLING_INTERVAL="3"
PROCESSES_CPU_SAMPLING_INTERVAL="1"
IDLE_DURATION="$((MONITORING_DURATION - DISK_LOAD_DURATION))"
DATA_FOLDER="data"
TOTAL_CPU_TXT_PATH="$DATA_FOLDER/cpu-total.txt"
TOTAL_CPU_PNG_PATH="$DATA_FOLDER/cpu-total.png"
PROCESSES_CPU_FOLDER_PATH="$DATA_FOLDER/cpu_proc_log"

# Function to run program to load the disk
run_disk_load() {
    cd data
    local data_folder="$1"
    fio --name=write_test \
        --ioengine=sync \
        --iodepth=64 \
        --rw=write \
        --bs=4k \
        --size=3G \
        --numjobs=1 \
        --runtime="$DISK_LOAD_DURATION" \
        --time_based \
        --group_reporting > /dev/null
    cd ..
}

# Function to collect total CPU usage using sar
collect_total_cpu_metrics() {
    local monitoring_duration="$1"
    local sampling_interval="$2"
    local output_txt_path="$3"
    local number_of_samples="$((monitoring_duration / sampling_interval))"
    sar -u "$sampling_interval" "$number_of_samples" | grep -v -E "CPU|Average|^$" > $output_txt_path
}

# Function to collect top CPU processes
collect_top_cpu_processes_usage() {
    local monitoring_duration="$1"
    local sampling_interval="$2"
    local output_dir="$3"
    local top_n_processes=18

    start_time=$(date +%s)
    current_time=$(date +%s)

    # Recreate the output directory on every script start
    rm -rf "$output_dir"
    mkdir -p "$output_dir"
     
    while ((current_time - start_time < monitoring_duration)); do
        # Run the command to get top CPU processes and save it to a text file
        ps -eo pcpu,pid,user,args --sort=-pcpu \
            | awk '{cmd=""; for(i=4;i<=NF;i++){cmd=cmd" "$i}; cmd=substr(cmd,1,100); printf "%-8s %-8s %-8s %-20s\n", $1, $2, $3, cmd}' \
            | head -n "$top_n_processes" > "$output_dir/$(date +%H-%M-%S).txt"
        sleep 1
        current_time=$(date +%s)
    done
}


rm -rf "$DATA_FOLDER"
mkdir -p "$DATA_FOLDER"

echo
echo "**************"
echo "Test start: $(date +%T)"
echo "Monitoring duration: $(( MONITORING_DURATION / 60)) min ($(( IDLE_DURATION / 60)) min without disk load)"

run_disk_load $DATA_FOLDER &
collect_total_cpu_metrics "$MONITORING_DURATION" "$TOTAL_CPU_SAMPLING_INTERVAL" $TOTAL_CPU_TXT_PATH &
collect_top_cpu_processes_usage "$MONITORING_DURATION" "$PROCESSES_CPU_SAMPLING_INTERVAL" $PROCESSES_CPU_FOLDER_PATH

echo "[$(date +%H:%M:%S)] Finished collecting metrics"

echo "Converting CPU metrics to visual representation..."
sleep 1
./scripts/create_video.py
echo "[$(date +%H:%M:%S)] Test end"
echo "[$(date +%H:%M:%S)] Result CPU usage video: $(pwd)/cpu.mp4"
