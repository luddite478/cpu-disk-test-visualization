from datetime import datetime, timedelta

def convert_to_seconds(time1, time2):
    # Parse the time arguments into datetime objects
    dt1 = datetime.strptime(time1, '%H-%M-%S')
    dt2 = datetime.strptime(time2, '%H-%M-%S')

    # Remove seconds from the datetime objects
    dt1_prev_minute = dt1.replace(second=0)
    dt2_next_minute = dt2.replace(second=0) + timedelta(minutes=1)

    # Calculate the time difference in seconds
    seconds1 = (dt1_prev_minute - datetime.min).total_seconds()
    seconds2 = (dt2_next_minute - datetime.min).total_seconds()

    return seconds1, seconds2

start, end = convert_to_seconds('10-20-59', '10-21-30')
sec_range = end - start

print(e-s)