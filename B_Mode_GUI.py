import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import serial
import time
from scipy.signal import hilbert, chirp
import timeit, functools
import numpy as np
import threading

root = tkinter.Tk()
root.wm_title("REVO B-MODE Imaging Software")

stopper = True
quitter = False
modeVar = True

No = 2*16
ser = serial.Serial('COM3', 8*1000000, timeout=1)  # open serial port

ser.set_buffer_size(rx_size = 2048*2*16, tx_size = 10)


ser.flushInput()
ser.flushOutput()



fig = plt.figure(figsize=(2,4), dpi=180)

root.img =  np.random.rand(1024,32)
image = plt.imshow(root.img, cmap='gray',interpolation='nearest',animated=False,extent=[0,31* 0.3,1024*1.498*0.5*(1/20),0], aspect=1)

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)



def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    # root.quit()     # stops mainloop
    global quitter
    quitter = True
    
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate

def _toggle():
    global stopper
    stopper = not stopper
    button_stop.config(text= 'Stop' if stopper else 'Start')


def _mode():
    global modeVar
    modeVar = not modeVar
  
                  

def _update(ser):
    t0 = time.time()
    global stopper

    
    if stopper == True:
            

        
        ser.write(b'a')

        data = ser.read(2048*No)
        
        
        assert len(data) == 2048*No , 'Connection issue we got '+ str(len(data)) + ' Instead of ' + str(2048*No)
        data1 = np.frombuffer(data, dtype=np.int16, count=-1).reshape(No,-1)
        data2 = np.abs(hilbert(data1.T-np.mean(data1,axis=1)))
        data3 = 20*np.log10(data2)
    

        # assert ser.inWaiting() == 0 , 'unread packages '

        root.img = data2 if modeVar else data3
        image.set_clim(vmin=root.img.min(), vmax=root.img.max())
        image.set_data(root.img)
        canvas.draw()
        t1 = time.time()
        text = 'fps: ' + "{:.2f}".format(1/(t1-t0)) + ' Hz'
        label.config(text=text, width=len(text))
        
        

prompt = 'fps'
label = tkinter.Label(master= root, text=prompt, width=len(prompt))
label.pack(side=tkinter.TOP)

button = tkinter.Button(master=root, text="Quit", command=_quit)
button_stop = tkinter.Button(master=root, text="Stop", command=_toggle)
button_Mode = tkinter.Button(master=root, text="Mode", command=_mode)

button.pack(side=tkinter.LEFT)
button_stop.pack(side=tkinter.LEFT )
button_Mode.pack(side=tkinter.LEFT )



while not quitter :
    root.update()
    if quitter:
        break
    _update(ser)

   

