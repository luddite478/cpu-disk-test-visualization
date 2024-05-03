#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y fio sysstat gnuplot ffmpeg python3-pip dos2unix
pip install Pillow

MONITORING_DURATION="30"
DISK_LOAD_DURATION="30"
TOTAL_CPU_SAMPLING_INTERVAL="1"
PROCESSES_CPU_SAMPLING_INTERVAL="1"
IDLE_DURATION="$((MONITORING_DURATION - DISK_LOAD_DURATION))"
DATA_FOLDER="data"
TOTAL_CPU_TXT_PATH="$DATA_FOLDER/cpu-total.txt"
TOTAL_CPU_PNG_PATH="$DATA_FOLDER/cpu-total.png"
PROCESSES_CPU_FOLDER_PATH="$DATA_FOLDER/cpu_processes_log"

echo
echo "**************"
echo "Test start: $(date +%T)"
echo "Monitoring duration: $(( MONITORING_DURATION / 60)) min ($(( IDLE_DURATION / 60)) min without disk load)"

# Function to run program to load the disk
run_disk_load() {
    cd data
    local data_folder="$1"
    fio --name=write_test \
        --ioengine=sync \
        --iodepth=64 \
        --rw=write \
        --bs=4k \
        --size=5G \
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
monitor_top_cpu_processes() {
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
            | awk '{cmd=""; for(i=4;i<=NF;i++){cmd=cmd" "$i}; cmd=substr(cmd,1,20); printf "%-8s %-8s %-8s %-20s\n", $1, $2, $3, cmd}' \
            | head -n "$top_n_processes" > "$output_dir/top-cpu-$(date +%H-%M-%S).txt"
        sleep 1
        current_time=$(date +%s)
    done
}

# Function to generate CPU usage plot from sar output
generate_total_cpu_plot() {
    local total_cpu_txt_path="$1"
    local total_cpu_png_path="$2"
    gnuplot -persist << EOF
    reset
    # Graph terminal and general config
    set terminal pngcairo enhanced font 'Verdana,8'
    set output "$total_cpu_png_path"
    set title "CPU usage graph"
    set key bmargin
    # Styles for different lines
    set style line 1 lc rgb '#e74c3c' pt 1 ps 1 lt 1 lw 2 # line1
    set style line 2 lc rgb '#3498db' pt 6 ps 1 lt 1 lw 2 # line2
    # Axis configuration
    set style line 11 lc rgb '#2c3e50' lt 1 lw 1.5 # Axis line
    set border 3 back ls 11
    set tics nomirror
    set autoscale xy
    set xdata time
    set timefmt "%H:%M:%S"
    set format x "%H:%M"
    set xlabel "Time"
    set ylabel "CPU %"
    # Background grid
    set style line 11 lc rgb '#aeb6bf' lt 0 lw 2
    set grid back ls 11
    # Begin plotting
    plot "$total_cpu_txt_path" using 1:3 title 'User%' with l ls 1, \
        ''                   using 1:5 title 'System%' with l ls 2
EOF
}

rm -rf "$DATA_FOLDER"
mkdir -p "$DATA_FOLDER"

run_disk_load $DATA_FOLDER &

collect_total_cpu_metrics "$MONITORING_DURATION" "$TOTAL_CPU_SAMPLING_INTERVAL" $TOTAL_CPU_TXT_PATH &

monitor_top_cpu_processes "$MONITORING_DURATION" "$PROCESSES_CPU_SAMPLING_INTERVAL" $PROCESSES_CPU_FOLDER_PATH

echo "Test end: $(date +%H:%M:%S)"

sleep 1

echo "Creating a total CPU utilisation plot..."
generate_total_cpu_plot $TOTAL_CPU_TXT_PATH $TOTAL_CPU_PNG_PATH

echo "Creating a final CPU usage video..."

dos2unix create_video.py 2> /dev/null
./create_video.py

echo "Result CPU usage video: $(pwd)/cpu.mp4"

#rm -rf data