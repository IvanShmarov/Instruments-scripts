import tkinter
import visa
import threading
import time

root = tkinter.Tk()
root.title("Control unit")

# IMPORTANT VARIABLES
KeithleyReadyStatus = tkinter.BooleanVar()
KeithleyReadyStatus.set(False)

StartVoltageEntryValue = tkinter.StringVar()
StartVoltageEntryValue.set("0.0")

EndVoltageEntryValue = tkinter.StringVar()
EndVoltageEntryValue.set("1.0")

CurrentLimitValue = tkinter.StringVar()
CurrentLimitValue.set("25e-3")

TimeIncrementEntryValue = tkinter.StringVar()
TimeIncrementEntryValue.set("10e-3")

NumberOfPointsEntryValue = tkinter.StringVar()
NumberOfPointsEntryValue.set("101")

BothWayScan = tkinter.BooleanVar()
BothWayScan.set(False)

ScanningStatus = tkinter.BooleanVar()
ScanningStatus.set(False)

RAW_DATA = ""


# IMPORTANT VARIABLES END

# INSTRUMENTS

Keithley = None

Mercury = None

# INSTUMENTS END

# FUNCTIONS
def FUNC_SCAN_BUTTON(*args):
    global KeithleyReadyStatus
    global ScanningStatus
    print("Scan Button Pressed" , args)
    if KeithleyReadyStatus.get():
        ScanningStatus.set(True)
        ScanningThread = threading.Thread(target=THREAD_SCAN)
        ScanningThread.start()
    

def FUNC_SWAP_BUTTON(*args):
    global StartVoltageEntryValue
    global EndVoltageEntryValue
    print("Swap Button Pressed", args)
    temp_string = StartVoltageEntryValue.get()
    StartVoltageEntryValue.set(EndVoltageEntryValue.get())
    EndVoltageEntryValue.set(temp_string)

def FUNC_KEITHLEY_STATUS_CHANGE(*args):
    global KeithleyReadyStatus
    global KeithleyStatusLabel
    print(args)
    if KeithleyReadyStatus.get():
        KeithleyStatusLabel["text"] = "Ready"
        KeithleyStatusLabel["bg"] = "#00ff00"
    else:
        KeithleyStatusLabel["text"] = "Not Ready"
        KeithleyStatusLabel["bg"] = "#ff0000"

def FUNC_SCANNING_STATUS_CHANGE(*args):
    global ScanningStatus
    global ScanButton
    print(args)
    if ScanningStatus.get():
        ScanButton["state"] = tkinter.DISABLED
        ScanButton["text"] = "Scanning"
        ScanButton["bg"] = "#ff0000"
    else:
        DataProcessingThread = threading.Thread(target=THREAD_DATA_PROCESSING)
        DataProcessingThread.start()
        ScanButton["state"] = tkinter.NORMAL
        ScanButton["text"] = "SCAN"
        ScanButton["bg"] = "#00ff00"

def FUNC_CANVAS_INI():
    global ResultCanvas
    ResultCanvas.create_line(10,
                      490,
                      490,
                      490,
                             tags=("axis","yaxis"))
    ResultCanvas.create_line(10,
                      10,
                      10,
                      490,
                             tags=("axis","xaxis"))
    
    
# FUNCTIONS END

# THREADS
def THREAD_FIND_KEITHLEY():
    global Keithley
    global KeithleyReadyStatus

    # Creating a resource manager
    ResMan = visa.ResourceManager()
    # Getting the list of all instruments
    list_of_instruments = ResMan.list_resources()
    # Setting keithley initial address to the empty string
    keithley_addr = ""

    # Check all instruments from the instrument list
    for item in list_of_instruments:
        # This is the keithley specific chink of address
        if ("::0x05e6::0x2450::" in item.lower()):
            # If it fits, set it to keithley address
            keithley_addr = item
            # No need to search for keithley anymore, assume only one keithley connected
            break
    # If the address is not empty, try to connect to it
    if keithley_addr:
        Keithley = ResMan.open_resource( keithley_addr )
    # Check that Keithley is succesfully connected
    if Keithley:
        print("Found Keithley: ", Keithley.query("*IDN?"))
        Keithley.timeout = 60000
        KeithleyReadyStatus.set(True)
    else:
        print("Keithley was not found")
        KeithleyReadyStatus.set(False)


def THREAD_SCAN():
    global Keithley
    global KeithleyReadyStatus
    global StartVoltageEntryValue
    global EndVoltageEntryValue
    global CurrentLimitValue
    global TimeIncrementEntryValue
    global NumberOfPointsEntryValue
    global BothWayScan
    global ScanningStatus
    global RAW_DATA
    print("Constructing a command")
    command = """*RST;
TRAC:MAKE \"IVAN_BUFFER\", 300;
SOUR:FUNC VOLT;
SOUR:VOLT:RANG 20;
SOUR:VOLT:ILIM  0.02;
SENS:FUNC "CURR";
"""
    command += "SENS:CURR:RANG " + CurrentLimitValue.get() + ";\n"
    sweep_command = "SOUR:SWE:VOLT:LIN "
    sweep_command += StartVoltageEntryValue.get() + ", "
    sweep_command += EndVoltageEntryValue.get() + ", "
    sweep_command += NumberOfPointsEntryValue.get() + ", "
    sweep_command += TimeIncrementEntryValue.get() + ", 1, BEST, OFF, "
    if BothWayScan.get():
        sweep_command += "ON, "
    else:
        sweep_command += "OFF, "
    sweep_command += "\"IVAN_BUFFER\";"
    command += sweep_command + "\n"
    command += "INIT;\n*WAI;"
    print("The command is \n", command)
    Keithley.write(command)
    print("Command is sent, waiting for the data_lenght...")
    data_len = Keithley.query("TRAC:ACT? \"IVAN_BUFFER\";")[:-1]
    print("Data length is ", data_len)
    RAW_DATA = Keithley.query("TRAC:DATA? 1, " + data_len
                                + ", \"IVAN_BUFFER\", SOUR, READ, REL;")
    #Keithley.write("*RST")
    ScanningStatus.set(False)

def THREAD_DATA_PROCESSING():
    global RAW_DATA
    global ResultCanvas
    global BothWayScan
    Both = BothWayScan.get()
    print("Processing Results")
    if RAW_DATA:
        # EXTRACTING DATA
        V = [float(item) for item in RAW_DATA.split(",")[0::3]]
        I = [float(item) for item in RAW_DATA.split(",")[1::3]]
        t = [float(item) for item in RAW_DATA.split(",")[2::3]]
        # DO SOMETHING WITH DATA
        print("Time it took: ", t[-1])

        # PLOT DATA
        ResultCanvas.delete(*ResultCanvas.find_withtag("plot"))

        if max(V) != min(V) and max(I) != min(I):
    
            x_points = [10 + (v - min(V))/(max(V) - min(V))*480 for v in V]
            y_points = [490 - (i - min(I))/(max(I) - min(I))*480 for i in I]
            ox = 10 - 480*min(V)/(max(V) - min(V))
            oy = 490 + 480*min(I)/(max(I) - min(I))

            if Both:
                half_len = round(len(x_points)/2)
                ResultCanvas.create_line(list(zip(x_points[:half_len+1],y_points[:half_len+1])),
                                         tags="plot",
                                         fill="#0000ff")
                ResultCanvas.create_line(list(zip(x_points[half_len:],y_points[half_len:])),
                                         tags="plot",
                                         fill="#00ff00")
            else: 
                ResultCanvas.create_line(list(zip(x_points,y_points)),
                                         tags="plot",
                                         fill="#0000ff")

            ResultCanvas.create_line(10,oy,490,oy,
                                    fill="#ff0000",
                                    tags="plot",
                                    dash=(10,5))
            ResultCanvas.create_line(ox,10,ox,490,
                                    fill="#ff0000",
                                    tags="plot",
                                    dash=(5,10))

            
            
            ResultCanvas.create_text(15,490, text=str(V[0]), tags="plot",
                                     anchor = tkinter.NW)
            ResultCanvas.create_text(440,490, text=str(V[-1]), tags="plot",
                                     anchor = tkinter.NW)

            ResultCanvas.create_text(15,470, text=str(I[0]), tags="plot",
                                     anchor = tkinter.NW)
            ResultCanvas.create_text(15,10, text=str(I[-1]), tags="plot",
                                     anchor = tkinter.NW)
            
        print("Results are processed")

# THREADS END

# FRAMES
StatusFrame = tkinter.LabelFrame(root)
StatusFrame["text"] = "Status"

ControlFrame = tkinter.LabelFrame(root)
ControlFrame["text"] = "Control"

ResultFrame = tkinter.LabelFrame(root)
ResultFrame["text"] = "Result"

StatusFrame.grid(row=0,column=0)
ControlFrame.grid(row=1,column=0)
ResultFrame.grid(row=0,column=1,rowspan=2)
# FRAMES END

# STATUS FRAME
tkinter.Label(StatusFrame, text="Keithley: ").grid(row=0,column=0)
KeithleyStatusLabel = tkinter.Label(StatusFrame, text="Pending", bg="#ff0000")
KeithleyStatusLabel.grid(row=0,column=1)
KeithleyReadyStatus.trace("w", FUNC_KEITHLEY_STATUS_CHANGE)

tkinter.Label(StatusFrame, text="Mercury: ").grid(row=1,column=0)
MercuryStatusLabel = tkinter.Label(StatusFrame, text="Not supported Yet",
                                   bg="#ffff00")
MercuryStatusLabel.grid(row=1,column=1)
# STATUS FRAME END

# CONTROL FRAME
tkinter.Label(ControlFrame, text="Start Voltage: ").grid(row=0,column=0)
StartVoltageEntry = tkinter.Entry(ControlFrame, textvariable=StartVoltageEntryValue)
StartVoltageEntry.grid(row=0,column=1)

tkinter.Label(ControlFrame, text="End Voltage: ").grid(row=1,column=0)
EndVoltageEntry = tkinter.Entry(ControlFrame, textvariable=EndVoltageEntryValue)
EndVoltageEntry.grid(row=1,column=1)

tkinter.Label(ControlFrame, text="Current Limit: ").grid(row=2,column=0)
CurrentLimitEntry = tkinter.Entry(ControlFrame, textvariable=CurrentLimitValue, bg="#ffdddd")
CurrentLimitEntry.grid(row=2,column=1)

SwapButton = tkinter.Button(ControlFrame, text="Swap start and end voltages",
                            command=FUNC_SWAP_BUTTON)
SwapButton["width"] = 25
SwapButton["height"] = 2
SwapButton["bg"] = "#ECF7FF"
SwapButton.grid(row=3,column=0,columnspan=2)

tkinter.Label(ControlFrame, text="Time increment: ").grid(row=4,column=0)
TimeIncrementEntry = tkinter.Entry(ControlFrame, textvariable=TimeIncrementEntryValue)
TimeIncrementEntry.grid(row=4,column=1)

tkinter.Label(ControlFrame, text="Number of points: ").grid(row=5,column=0)
NumberOfPointsEntry = tkinter.Entry(ControlFrame,
                                    textvariable=NumberOfPointsEntryValue)
NumberOfPointsEntry.grid(row=5,column=1)

BothWayScanCheckButton = tkinter.Checkbutton(ControlFrame, text="Scan forward and backward",
                                             variable = BothWayScan, offvalue=False,
                                             onvalue=True)
BothWayScanCheckButton.grid(row=6,column=0,columnspan=2)


ScanButton = tkinter.Button(ControlFrame, text="SCAN", command=FUNC_SCAN_BUTTON)
ScanButton["width"] = 25
ScanButton["height"] = 2
ScanButton["bg"] = "#00ff00"
ScanButton.grid(row=7,column=0,columnspan=2)
# CONTROL FRAME END

# RESULT FRAME
ResultCanvas = tkinter.Canvas(ResultFrame)
ResultCanvas["width"] = 500
ResultCanvas["height"] = 500
ResultCanvas["bg"] = "white"
ResultCanvas.pack()
# RESULT FRAME END

# INI AREA
FindKeithleyThread = threading.Thread(target=THREAD_FIND_KEITHLEY, name="FINDING KEITHLEY")
FindKeithleyThread.start()

FUNC_CANVAS_INI()

ScanningStatus.trace("w", FUNC_SCANNING_STATUS_CHANGE)

# INI AREA END

# TEST AREA


# TEST AREA END

root.mainloop()
