#!/usr/bin/env python

import time

import Tkinter as tk
import matplotlib 
matplotlib.use('TkAgg') 

from numpy import arange, sin, pi , cos 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg 
from matplotlib.figure import Figure 

def format_date(x, pos=None):
    return time.strftime('%Y-%m-%d',time.localtime(x))

class Gui(object):
    def __init__(self,master, name=None, dbfile=None):
        self.master = master
        print name,dbfile
        import omron
        # self.omron = omron.Omron()
        self.omron = None

        self.name = name

        self.data = None
        self.processed = None
        self.use_processed = False
        self.dbfile = dbfile
        if self.dbfile: self.open_file()

        # frame = tk.Frame(master)
        # frame.pack()

        menubar = tk.Menu(master)
        menubar.add_command(label="Quit", command=master.quit)
        menubar.add_command(label="Open", command=self.open_file)
        menubar.add_command(label="Plot", command=self.update_plot)
        menubar.add_command(label="Sync", command=self.sync)
        menubar.add_command(label="Avg", command=self.average)

        #menubar.pack()

        master.config(menu=menubar)

        self.figure = Figure(figsize=(5,4),dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.canvas.show() 
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1) 

        self.update_plot()

        return

    def open_file(self):
        'If given a file, open it, else prompt user'
        import store
        if self.dbfile:
            print 'Loading DB file %s using name %s'%(self.dbfile,self.name)
            self.data = store.Data(self.dbfile,self.name)
            return

        from tkFileDialog import askopenfilename
        self.dbfile = askopenfilename()
        if not self.dbfile: 
            print 'Canceled'
            return
        return self.open_file()
            

    def update_plot(self):
        'Update the plot given current parameters'
        if not self.data: 
            print "Can't plot, no data"
            return
        if self.use_processed:
            print 'Plotting processed data'
            rows = self.processed
        else:
            print 'Plotting all data'
            rows = self.data.all()

        import matplotlib.ticker as ticker

        # Convert row based to column based
        ts = list()
        sys = list()
        dia = list()
        pulse = list()
        for row in rows: 
            ts.append(row[0])
            sys.append(row[1])
            dia.append(row[2])
            pulse.append(row[3])
            continue

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(ts, sys, 'k-', ts, dia, 'b-', ts, pulse, 'r')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        self.figure.autofmt_xdate()
        self.canvas.show() 

        return

    def sync(self): 
        print 'sync() not implemented'
        return

    def average(self,window=600):
        'Respond to Avg button, average nearby data in window (seconds)'
        rows = self.data.all()
        new_rows = []
        count = 0
        last_time = sys_sum = dia_sum = pulse_sum = 0
        for row in rows:
            dt = row[0] - last_time
            last_time = row[0]
            if dt > window:     # save accumulated and start new with current
                if count:       # first time through
                    new_rows.append((last_time,sys_sum/count,dia_sum/count,pulse_sum/count))
                count = 1
                sys_sum = row[1]
                dia_sum = row[2]
                pulse_sum = row[3]
                continue
            # we are inside window of last data, accumulate
            count += 1
            sys_sum += row[1]
            dia_sum += row[2]
            pulse_sum += row[3]
            continue
        print 'Averaged %d values down to %d'%(len(rows),len(new_rows))
        self.processed = new_rows
        self.use_processed = True
        self.update_plot()
        return            

    pass


class Main(object):
    def __init__(self,argv=None):
        import optparse
        parser = optparse.OptionParser()
        parser.add_option('-f','--file',type='string',default=None,
                          help='Set the SQLite3 data file')
        parser.add_option('-n','--name',type='string',default='omron',
                          help='Set a short name to distinguish the data between individuals')
        parser.add_option('-d','--device',type='string',default=None,
                          help='Set the USB device file, overrides OMRON_DEV environment variable')
        self.parser = parser
        if argv:
            self.parse_args(argv)
        return

    def parse_args(self,argv):
        self.opts,self.args = self.parser.parse_args(argv)
        return

    pass

if '__main__' == __name__:

    import sys
    main = Main(sys.argv)
    print main.opts
    if main.opts.device:
        os.environ['OMRON_DEV'] = main.opts.device

    import device
    dev = device.device()
    if dev:
        print 'Using device: "%s"'%dev
    else:
        print 'No device autodetected, try running "lsusb" and setting OMRON_DEV=/dev/bus/usb/BBB/DDD'
    root = tk.Tk()
    app = Gui(root,main.opts.name,main.opts.file)
    root.mainloop()
    