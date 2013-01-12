# Simple gui application that works with pyrow to log workout
# information sent from a connected Concept 2 rowing erg.

import Tkinter  # gui kit
import pyrow    # handles connection to ergs
import time     # for sleep
import datetime # for getting date and time (write to logs)

def main():
    # find any connected ergs
    connected_ergs = pyrow.find()
    if len(connected_ergs) == 0:
        exit("No ergs found.")
        
    # get the first connected erg and print its status
    erg = pyrow.pyrow(connected_ergs[0])
    erg_info = pyrow.pyrow.getErg(erg)
    erg_status = pyrow.pyrow.getStatus(erg)
    
    print "Concept 2 erg connected (model %s, serial: %r)" % (erg_info['model'], erg_info['serial'])
    
    # wait for a workout to begin on the erg
    workout = erg.getWorkout()
    print "Waiting for workout to begin..."
    while workout['state'] == 0:
        time.sleep(1)
        workout = erg.getWorkout()
    print "Workout has begun..."
    
    workout_data = log_workout(erg, workout)
    
    print "Workout over."
    
    # get force data and convert into normalised graph coords
    if len(workout_data) > 0:
        plot_force_curves(workout_data, 0, len(workout_data))
        now = datetime.datetime.now()
        filename = "workout_" + now.strftime("%Y%m%d_%H%M") + ".csv"
        export_workout_data(workout_data, filename)
    else:
        print "Error: No strokes recorded. Cannot show data."

def export_workout_data(workout_data, filename):
    """Exports workout data to a .csv file"""
    outfile = open(filename, 'w')
    outfile.write("Time,Distance,SPM,Pace,Force Plot\n")
    for stroke in workout_data:
        m = stroke['monitor']   # monitor data
        f = stroke['force']     # force plot
        m_str = str(m['time']) + "," + str(m['distance']) + "," + str(m['spm']) + "," + str(m['pace']) + ","
        f_str = ",".join([str(i) for i in f]) 
        outfile.write(m_str + f_str + "\n")
    outfile.close()
    print "Workout log written to file \'%s\'." % filename

def clamp(val, minval, maxval):
    if val < minval: return minval
    if val > maxval: return maxval
    return val

def plot_force_curves(workout_data, first, last):
    """Plots all force curves in a set of workout data within the specified range"""
    first = clamp(first, 0, len(workout_data))
    last = clamp(last, 0, len(workout_data))
    
    # create a little window with a canvas
    top = Tkinter.Tk()
    # top.tile("Force Curves")
    window_width = 320
    window_height = 256
    canvas = Tkinter.Canvas(top, bg = "black", width = window_width, height = window_height)
    
    # plot first stroke in red
    plot_force_curve(workout_data[0]['force'], canvas, window_width, window_height, "red")
    # plot other strokes in default colour
    for stroke in range(first + 1, last):
        force_data = workout_data[stroke]['force']
        if len(force_data) > 1:
            plot_force_curve(force_data, canvas, window_width, window_height)
    
    canvas.pack()
    top.mainloop()    
    
    
def plot_force_curve(force_data, canvas, window_width, window_height, line_color = "green"):
    # process data into a list of x and y coordinates scaled by window size
    plot = []
    f_max = float(max(force_data))
    num_points = float(len(force_data))
    for i, f in enumerate(force_data):
        x = float(i) / num_points * window_width
        y = window_height - float(f) / f_max * window_height
        plot.append(x)
        plot.append(y)

    # plot the force curve
    canvas.create_line(plot, fill = line_color)


def log_workout(erg, workout):
    """Logs a workout and returns the data as a list of strokes (monitor, force) when finished."""
    strokes = [] # store all strokes in here
    
    total_time = 0
    total_distance = 0
    # stay in this loop until the workout ends
    while workout['state'] == 1:
        forceplot = erg.getForcePlot()
        # wait for the start of the drive
        while forceplot['strokestate'] != 2 and workout['state'] == 1:
            forceplot = erg.getForcePlot()
            workout = erg.getWorkout()
        
        # record force data during the drive
        force = forceplot['forceplot']  # start of pull (when strokestate first changed to 2)
        monitor = erg.getMonitor()      # get monitor data for start of stroke
        
        # loop during drive
        while forceplot['strokestate'] == 2:
            forceplot = erg.getForcePlot()
            force.extend(forceplot['forceplot'])
        else:
            # get force data from end of stroke
            forceplot = erg.getForcePlot()
            force.extend(forceplot['forceplot'])

        total_time += monitor['time']
        total_distance += monitor['distance']
        
        print "[%d] time: %s, distance: %s, pace: %s" % (len(strokes) + 1, monitor['time'], monitor['distance'], monitor['pace'])
        # print " force [ %s ]" % (",".join([str(f) for f in force]))

        # write stroke data to strokes
        stroke = { 'monitor' : monitor, 'force' : force }
        strokes.append( stroke )

        # update workout (so the loop exits when the workout is over)    
        workout = erg.getWorkout()
    
    return strokes

main()
