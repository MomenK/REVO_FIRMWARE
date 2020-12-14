import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import multiprocessing

import serial
import time
from scipy.signal import hilbert, chirp
import timeit, functools


def plot():
    global canvas, toolbar, image
    

    fig = plt.figure(figsize=(2,4), dpi=180)
    img =  np.zeros((1024,32))
    image = plt.imshow(img, cmap='gray',interpolation='nearest',animated=False,extent=[0,31* 0.3,1024*1.498*0.5*(1/20),0], aspect=1)

    canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    canvas.mpl_connect("key_press_event", on_key_press)

def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)





def _quitAll(process, top):
    global quitter
    quitter = True
    process.terminate()
    top.quit()
    top.destroy()




def Serial_fetcher(q,q_enabler,q_fps):
    No = 2*16
    ser = serial.Serial('COM3', 8*1000000, timeout=1)  # open serial port
    ser.flushInput()
    ser.flushOutput()
    enabler = True
    t1 = 0
    while True:
        if not q_enabler.empty():
            enabler = q_enabler.get_nowait()
        else:
            enabler = enabler

        if  enabler== True:
            t0 = time.time()
            ser.write(b'a')

            data = ser.read(2048*No)
            
            
            assert len(data) == 2048*No , 'Connection issue we got '+ str(len(data)) + ' Instead of ' + str(2048*No)
            data1 = np.frombuffer(data, dtype=np.int16, count=-1).reshape(No,-1)
            data2 = np.abs(hilbert(data1.T-np.mean(data1,axis=1)))


            q.put(data2)
            old_t1 = t1
            t1 = time.time()
            # text = 'fps: ' + "{:.2f}".format(1/(t1-t0)) + ' Hz'
            text = 'fps: ' + "{:.2f}".format(1/(t1-old_t1)) + ' Hz'
            q_fps.put(text)
            # print(1/(t1-old_t1))
        # else:

        #     time.sleep(0.1)



def updateplot(q,q_fps):
    
    try:       
        
        result=q.get_nowait()
    
        result_log = 20*np.log10(result)
        DataToPlot =  result if modeVar else result_log
        
        image.set_data(DataToPlot)
        image.set_clim(vmin=DataToPlot.min(), vmax=DataToPlot.max())

        canvas.draw()
        text = q_fps.get_nowait()
        label.config(text=text, width=len(text))
        root.after(1,updateplot,q,q_fps)
    
    except:
     
        root.after(1,updateplot,q,q_fps)


def _mode():
    global modeVar
    modeVar = not modeVar

def _toggle():
    global stopper
    stopper = not stopper
    q_enabler.put(stopper)
    button_stop.config(text= 'Stop' if stopper else 'Start')

if __name__ == '__main__':
    modeVar = True
    stopper = True
    root = tkinter.Tk()

    q = multiprocessing.Queue()
    q_enabler = multiprocessing.Queue()
    q_enabler.put(stopper)
    q_fps = multiprocessing.Queue()
    simulate=multiprocessing.Process(None,Serial_fetcher,args=(q,q_enabler,q_fps))



    root.wm_title("Embedding in Tk")  
    root.protocol("WM_DELETE_WINDOW", lambda: _quitAll(simulate,root))
    plot()


    prompt = 'fps'
    label = tkinter.Label(master= root, text=prompt, width=len(prompt))
    label.pack(side=tkinter.TOP)

    button_quit = tkinter.Button(master=root, text="Quit", command=lambda: _quitAll(simulate,root))
    button_stop =tkinter.Button(master=root, text="Stop", command=_toggle)
    button_Mode = tkinter.Button(master=root, text="Mode", command=_mode)

    button_quit.pack(side=tkinter.LEFT)
    button_stop.pack(side=tkinter.LEFT)
    button_Mode.pack(side=tkinter.LEFT)
    
    
    
    simulate.start()

    updateplot(q,q_fps)
    
    root.mainloop()
    print('Done')
 











# def simulation(q):
#     # for i in iterations:
#     while True:
#         # print(i)
#         time.sleep(0.01)
#         q.put(np.random.rand(1024,32))
#     # q.put('Q')


# def _quit():
#     global quitter
#     quitter = True
#     root.quit()     # stops mainloop
#     root.destroy()  # this is necessary on Windows to prevent
#                     # 