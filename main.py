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


def _quitAll(process,M_process, top):
    global quitter
    quitter = True
    process.terminate()
    M_process.terminate()
    top.quit()
    top.destroy()

def _mode():
    global modeVar
    modeVar = not modeVar

def _toggle():
    global stopper
    stopper = not stopper
    q_enabler.put(stopper)
    button_stop.config(text= 'Stop' if stopper else 'Start')



def _Mtoggle():
    # global Mstopper
    # Mstopper = not Mstopper
    m_q_enabler.put(True)
    # print(Mstopper)
    button_stop.config(text= 'Stop' if stopper else 'Start')



def Serial_fetcher(q,q_enabler,q_fps):
    No = 2*16
    ser = serial.Serial('/dev/COM3', 8*1000000, timeout=1)  # open serial port
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

def M_Serial_fetcher(m_q,m_q_enabler):


    enabler = False
    counter = 0

    agg = np.empty((1024,0))
    No = 2*1
    ser = serial.Serial('/dev/COM4', 8*1000000, timeout=1, parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS) 
    ser.flushInput()
    ser.flushOutput()

    while True:
        if not m_q_enabler.empty():
            enabler = m_q_enabler.get_nowait()
            print(enabler)
        else:
            enabler = enabler


        if  enabler== True:
            ser.write(b'a')
            data = ser.read(2048*No)  
            assert len(data) == 2048*No , 'Connection issue we got '+ str(len(data)) + ' Instead of ' + str(2048*No)
            data1 = np.frombuffer(data, dtype=np.int16, count=-1).reshape(No,-1)
            data2 = np.abs(hilbert(data1.T-np.mean(data1,axis=1)))      
            agg = np.append(agg,data2,axis=1)
            counter=counter+1

            if counter == 1000:
                m_q.put(agg)
                enabler = False
                counter = 0
                print("Done")

                plt.close()
                plt.figure()
  
                Image = plt.imshow(agg,cmap='gray',interpolation='nearest', aspect='auto',animated=False)
                Image.set_clim(vmin=0, vmax=500)
                plt.show()
        
                
        else:
            agg = np.empty((1024,0))

    pass

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




if __name__ == '__main__':
    modeVar = True
    stopper = True
    Mstopper = False
    root = tkinter.Tk()

    q = multiprocessing.Queue()
    q_enabler = multiprocessing.Queue()
    q_enabler.put(stopper)
    q_fps = multiprocessing.Queue()

    simulate=multiprocessing.Process(None,Serial_fetcher,args=(q,q_enabler,q_fps))

    m_q = multiprocessing.Queue()
    m_q_enabler = multiprocessing.Queue()
    m_q_enabler.put(Mstopper)
   

    M_simulate=multiprocessing.Process(None,M_Serial_fetcher,args=(m_q,m_q_enabler))

    root.wm_title("Embedding in Tk")  
    root.protocol("WM_DELETE_WINDOW", lambda: _quitAll(simulate,M_simulate,root))
    plot()


    prompt = 'fps'
    label = tkinter.Label(master= root, text=prompt, width=len(prompt))
    label.pack(side=tkinter.TOP)

    button_quit = tkinter.Button(master=root, text="Quit", command=lambda: _quitAll(simulate,M_simulate,root))
    button_stop =tkinter.Button(master=root, text="Stop", command=_toggle)
    button_Mode = tkinter.Button(master=root, text="Mode", command=_mode)

    button_quit.pack(side=tkinter.LEFT)
    button_stop.pack(side=tkinter.LEFT)
    button_Mode.pack(side=tkinter.LEFT)

    button_M_stop =tkinter.Button(master=root, text="Stop", command=_Mtoggle)

    button_M_stop.pack(side=tkinter.RIGHT)

    
    
    
    simulate.start()

    updateplot(q,q_fps)

    M_simulate.start()
    
    root.mainloop()
    print('Done')
