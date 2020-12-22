import os, glob
import pandas as pd
import seaborn as sns
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.validators.scatter
import plotly.package_data.templates

sns.set()
current_dir = os.getcwd()

def absolute_value(val):
    a  = np.round(val/100.*sum(slices), 0)
    return int(a)

def time_to_minutes(str_time):
    ''' takes time string in format : '12:02 pm'
        returns int of minutes      :  722'''

    time, period= str_time.split(' ')
    hour, minute = map(int, time.split(':'))
    if period.lower() == 'pm' and hour < 12:
        hour += 12
    return hour*60 + minute

# need to convert back and forth to find earliest time
def minutes_to_time(int_min):
    ''' takes int of minutes: '722'
        returns str of time :  '12:02 pm' '''
    hour = int_min // 60
    mins = int((int_min / 60 - hour) * 60)
    if mins < 10: mins = "0" + str(mins)
    if hour >= 12:
        if hour > 12: hour -= 12
        return str(hour)+":"+str(mins)+" pm"
    return str(hour)+":"+str(mins)+" am"

def attendance_tracker(diff_tracker, enter_time, leave_time, email_tracker, email, num_meetings):
    '''takes:   dict of difference tracker for how many people entered/left at that minute
                enter and leave time from dataframe for dict keys
                email for tracking between multiple meetings'''
    # how many people left or entered during a given minute
    diff_tracker[enter_time] += 1
    diff_tracker[leave_time] -= 1

    # for multiple meetings
    if email in email_tracker:
        # to make sure multiple drop/joins don't go over possible number of meetings
        if email_tracker[email] < num_meetings:
                email_tracker[email] += 1
    else:
        email_tracker[email] = 1
    

# build list of file names and check
extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]

# list of dataframes for attendance data
# skips rows now part of data table
file_df_list = [pd.read_csv(f, sep="\t", skiprows=[0,1], encoding="utf-16-le") for f in all_filenames]

# dataframe for tracking stats of meetings
stat_cols = ["Event", "Attendees", "Avg Stay"]
event_stats = pd.DataFrame(columns=stat_cols)

# for trimming meeting based on start time
trim_times = {"no": 0, "yes": 1, "No": 0, "Yes": 1, "n": 0, "y": 1, "N": 0, "Y": 1}
print("Would you like to trim the attendance graph based on start times for each meeting?")
print("You will need to enter a time for each meeting.")
while True:
    try:
        trimmed = trim_times[input("yes/no: ")]
    except KeyError:
        print("Sorry, please only enter 'yes' or 'no'.")
        continue
    else:
        if trimmed:
            print("Only enter times in the format of 'HH:MM pm/am'")
        break

# loop to organize and export data
events = []           # list of col names from files
minute_lists = []   # list of lists with attendence number by the minute
num_attended = {}   # number of events attended by each person
avg_durations = []  # average attendee stay in each event
num_attendees = []  # how many people attended each event
num_meetings = len(all_filenames)
for i in range(num_meetings):
    # change event dates to names based on file names
    event = all_filenames[i][:len(all_filenames[i])-4]
    file_df_list[i].rename(columns={"Date": "Event"}, inplace = True)
    file_df_list[i]['Event'] = event
    events.append(event)

    # change 'Duration from string to int value
    file_df_list[i]['Duration'] = file_df_list[i]['Duration'].apply(lambda x: int(x.split(' ')[0]))

    # change start/stop time to minute value, lower all emails to same case
    file_df_list[i]['Start time'] = file_df_list[i]['Start time'].apply(time_to_minutes)
    file_df_list[i]['End time'] = file_df_list[i]['End time'].apply(time_to_minutes)
    file_df_list[i]['Email'] = file_df_list[i]['Email'].apply(lambda x: x.lower())

    # meeting start and end
    start = file_df_list[i]['Start time'].min()
    end = file_df_list[i]['End time'].max()
    diff = end - start

    # get valid input for starting time
    current_start = minutes_to_time(start) # need to convert back and forth to find minimum
    if trimmed:
        print("Current start time of ", event, "is ", current_start, ".")
        while True:
            try:
                start_time = time_to_minutes(input("New starting time: ")) - start
            except ValueError:
                print("Sorry, that time is not the correct format.")
                print("Valid time examples: '01:01 pm', '1:01 pm', '10:01 am'")
                continue
            else:
                break

    # create absolute minutes columns
    file_df_list[i]['Min Joined'] = file_df_list[i]['Start time'].apply(lambda x: x - start)
    file_df_list[i]['Min Left'] = file_df_list[i]['End time'].apply(lambda x: x - start)

    # initialize minutes counter
    diffs = [0] * (file_df_list[i]['Min Left'].max() + 1)
    mins = [0] * (file_df_list[i]['Min Left'].max() + 1)

    # iterate through attendees and add/subtract to minute attendance, track email attendance
    file_df_list[i].apply(lambda row: attendance_tracker(diffs, row['Min Joined'], row['Min Left'], \
                                                        num_attended, row['Email'], num_meetings), axis=1)
    
    duration_total = 0
    for index, row in file_df_list[i].iterrows():
        duration_total += row['Duration']
    
    # track average attendee stay for each meeting, round up
    duration_total = file_df_list[i]['Duration'].sum()
    unique_attendees = file_df_list[i]['Email'].nunique()
    avg_durations.append(-(-duration_total // unique_attendees))
    num_attendees.append(unique_attendees)
    
    # current attendees in meeting at specific minute
    total = 0
    for i in range(len(diffs)):
        total += diffs[i]
        mins[i] = total

    # null-out last minute to prevent "0" on graph
    mins[len(mins)-1] = np.nan

    # trim minutes to start times:
    if trimmed:
        mins = mins[start_time:]

    # preserve minutes attendance and duration average
    minute_lists.append(mins.copy())

# create folder for output
files_folder = current_dir + "\Output Files"
try:
    if not os.path.exists(files_folder):
        os.mkdir(files_folder)
except:
    print("Could not create new folder for output files; it may already exists.")
os.chdir(files_folder)

# PIE CHART GRAPH - sorting, for number of people that attended how many meetings
res = Counter(num_attended.values())
data = pd.DataFrame.from_records(list(sorted(res.items())), columns=['events attended','num people'])
slices = []
for key in res:
    slices.append(res[key])

# pie chart adjustments
pie, ax = plt.subplots(figsize=[12,12])
wedges, labels, autopct = plt.pie(x=data['num people'], labels=data['events attended'], 
                                    autopct=absolute_value, explode=[0.02]*len(data['num people']), 
                                    pctdistance=0.9, textprops={'fontsize': 12}, counterclock=False)
plt.setp(labels, fontsize=13, weight='bold')
plt.title("Number of Events Attended", fontsize=16, weight='bold')
plt.savefig('Number of Events Attended.png')

# ATTENDANCE GRAPH - by the minute
# extend minute lists to be of same length
longest = len(max(minute_lists, key=len))
for i in range(len(events)):
    minute_lists[i].extend(np.full(longest-len(minute_lists[i]),np.nan))

# name columns and assign minute attendances
df = pd.DataFrame()
for i in range(len(events)):
    df[events[i]] = minute_lists[i]

# create chart and adjust
fig = go.Figure([{
    'x': df.index,
    'y': df[col],
    'name': col
}  for col in df.columns])
fig.update_layout(autosize=False, width=1200, height=600,
                    xaxis_title='Time (minutes)',
                    yaxis_title='Attendees',
                    title='Number of Attendees by Meeting Minute',
                    legend_title='Meetings')
fig.update_xaxes(title_text='Time (minutes)')
fig.update_yaxes(title_text='Attendees')
fig.write_image("Event Attendance.png")
fig.show()
plt.show()

# make dataframe to pair data and save to CSV
stat_cols = ["Event", "Attendees", "Avg Stay(min)"]
event_stats = pd.DataFrame(list(zip(events, num_attendees, avg_durations)), columns=stat_cols)
event_stats.to_csv( "Event Stats.csv", index=False, encoding='utf-8-sig')

print("Summaries completed! Saved to 'Output Files' folder.")
input("Hit enter to exit.")