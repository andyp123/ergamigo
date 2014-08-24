# Simple gui application that works with pyrow to log workout
# information sent from a connected Concept 2 rowing erg.

# import Tkinter  # gui kit
import pyrow    # handles connection to ergs
import usb.core # for USBError
import time     # for sleep
import datetime # for getting date and time (write to logs)


def main():
    print "Welcome to ErgAmigo!"
    # find any connected ergs
    connected_ergs = pyrow.find()
    if len(connected_ergs) == 0:
        exit("No ergs found.")

    try:
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
        print "-- Starting workout --"
        print "User ID: %s" % workout['userid']
        print "Workout Type: %s" % workout['type']
        print "Workout State: %s" % workout['state']
        print "Interval Type: %s" % workout['inttype']
        print "Interval Count: %s" % workout['intcount']
        print "Machine Status: %s" % workout['status']
        print "----------------------"

        workout_data = log_workout(erg, workout)
    except usb.core.USBError as e:
        print "Error: Could not get data from erg."
        exit(e)


    print "Workout over."
    
    # get force data and convert into normalised graph coords
    if len(workout_data) > 0:
    #    plot_force_curves(workout_data, 0, len(workout_data))
        now = datetime.datetime.now()
        logdir = "./logs/"
        filename = "workout_" + now.strftime("%Y%m%d_%H%M") + ".csv"
        export_workout_data(workout_data, filename)
    else:
        print "Error: No strokes recorded. Cannot show data."


def import_workout_data(filename):
    """Import workout data from a csv file."""
    workout_data = []
    try:
        logfile = open(filename)
    except IOError as e:
        "Error: Could not open file \'" + filename + "\'."
    
    # define a stroke object to copy and populate with data
    line = logfile.readline()[:-1] # get field names from the first line (discarding '\n')
    field_names = line.split(',')

    line = logfile.readline()[:-1]
    while line != "":
        # get list of values
        values = line.split(',')
        # create empty stroke object
        stroke = { 'monitor': {}, 'forceplot': [] }
        m = stroke['monitor']
        f = stroke['forceplot']
        # populate stroke with values
        i = 0
        for fn in field_names:
            if fn != "forceplot":
                m[fn] = values[i]
            i += 1
        # get forceplot if available
        i = len(field_names) - 1
        if field_names[i] == "forceplot":
            for j in range(i,len(values)):
                f.append(values[j])
        # append stroke to workout data
        workout_data.append(stroke)
        line = logfile.readline()[:-1]

    return workout_data


def export_workout_data(workout_data, filename):
    """Exports workout data to a .csv file."""
    # construct a string of field headings
    # (output_forceplot and output_fields could later be changed to function arguments)
    output_forceplot = True
    output_fields = ["time","distance","spm","power","pace","calhr","calories","heartrate","status"]
    output_fields_str = ",".join([i for i in output_fields]) + (",forceplot\n" if output_forceplot else "\n")

    # write the data to a file line by line    
    outfile = open(filename, 'w')
    outfile.write(output_fields_str)

    for stroke in workout_data:
        m = stroke['monitor']
        m_str = ""
        for field_name in output_fields:
            m_str += str(m[field_name]) + ","

        if output_forceplot:
            f = stroke['forceplot']
            f_str = ",".join([str(i) for i in f]) 
            outfile.write(m_str + f_str + "\n")
        else:
            outfile.write(m_str[:-1] + "\n") # remove last ',' from m_str
    outfile.close()
    print "Workout log written to file \'%s\'." % filename


def clamp(val, minval, maxval):
    if val < minval: return minval
    if val > maxval: return maxval
    return val


# def plot_force_curves(workout_data, first, last):
#     """Plots all force curves in a set of workout data within the specified range"""
#     first = clamp(first, 0, len(workout_data))
#     last = clamp(last, 0, len(workout_data))
    
#     # create a little window with a canvas
#     top = Tkinter.Tk()
#     # top.tile("Force Curves")
#     window_width = 320
#     window_height = 256
#     canvas = Tkinter.Canvas(top, bg = "black", width = window_width, height = window_height)
    
#     # plot first stroke in red
#     plot_force_curve(workout_data[0]['forceplot'], canvas, window_width, window_height, "red")
#     # plot other strokes in default colour
#     for stroke in range(first + 1, last):
#         force_data = workout_data[stroke]['forceplot']
#         if len(force_data) > 1:
#             plot_force_curve(force_data, canvas, window_width, window_height)
    
#     canvas.pack()
#     top.mainloop()    
    
    
# def plot_force_curve(force_data, canvas, window_width, window_height, line_color = "green"):
#     # process data into a list of x and y coordinates scaled by window size
#     plot = []
#     f_max = float(max(force_data))
#     num_points = float(len(force_data))
#     for i, f in enumerate(force_data):
#         x = float(i) / num_points * window_width
#         y = window_height - float(f) / f_max * window_height
#         plot.append(x)
#         plot.append(y)

#     # plot the force curve
#     canvas.create_line(plot, fill = line_color)


def log_workout(erg, workout):
    """Logs a workout and returns the data as a list of strokes (monitor, force) when finished."""
    workout_data = [] # store all strokes in here
    
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
        
        print "[%d] time: %s, distance: %s, pace: %s" % (len(workout_data) + 1, monitor['time'], monitor['distance'], monitor['pace'])
        # print " force [ %s ]" % (",".join([str(f) for f in force]))

        # write stroke data to strokes
        stroke = { 'monitor' : monitor, 'forceplot' : force }
        workout_data.append( stroke )

        # update workout (so the loop exits when the workout is over)    
        workout = erg.getWorkout()
    
    print "workout: %r" % workout
    return workout_data


main()


def test():
    workout_data = import_workout_data("test.csv")
    export_workout_data(workout_data, "test_rexport.csv")
