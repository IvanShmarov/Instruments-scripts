import tkinter
import visa
import threading
import time
import math

root = tkinter.Tk()
root.title("Control unit")

# IMPORTANT VARIABLES
KeithleyReadyStatus = tkinter.BooleanVar()
KeithleyReadyStatus.set(False)

MercuryReadyStatus = tkinter.BooleanVar()
MercuryReadyStatus.set(False)

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

DrawOriginSettings = tkinter.StringVar()
DrawOriginSettings.set("SW")

DrawVoltageAxisRangeEntryValue = tkinter.StringVar()
DrawVoltageAxisRangeEntryValue.set("2.0")

DrawCurrentAxisRangeEntryValue = tkinter.StringVar()
DrawCurrentAxisRangeEntryValue.set("25e-3")

RAW_DATA = ""
Voltage = []
Current = []
delta_time = []


# IMPORTANT VARIABLES END

# INSTRUMENTS

ResMan = visa.ResourceManager()

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
    global ScanButton
    print(args)
    if KeithleyReadyStatus.get():
        KeithleyStatusLabel["text"] = "Ready"
        KeithleyStatusLabel["bg"] = "#00ff00"
    else:
        KeithleyStatusLabel["text"] = "Not Ready"
        KeithleyStatusLabel["bg"] = "#ff0000"
        ScanButton["state"] = tkinter.DISABLED
        ScanButton["text"] = "Keithley not found"
        ScanButton["bg"] = "#ff0000"

def FUNC_MERCURY_STATUS_CHANGE(*args):
    global MercuryReadyStatus
    global MercuryStatusLabel
    print(args)
    if MercuryReadyStatus.get():
        MercuryStatusLabel["text"] = "Ready"
        MercuryStatusLabel["bg"] = "#00ff00"
    else:
        MercuryStatusLabel["text"] = "Not Ready"
        MercuryStatusLabel["bg"] = "#ff0000"

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

def FUNC_REFRESH_INST_BUTTON(*args):
    FindKeithleyThread = threading.Thread(target=THREAD_FIND_KEITHLEY, name="FINDING KEITHLEY")
    FindMercuryThread = threading.Thread(target=THREAD_FIND_MERCURY, name="FINDING MERCURY")
    FindKeithleyThread.start()
    FindMercuryThread.start()
    


def FUNC_REDRAW_BUTTON():
    DrawThread = threading.Thread(target=THREAD_DRAW_DATA, name="DRAWING DATA")
    DrawThread.start()
    
    
    
# FUNCTIONS END

# THREADS
def THREAD_FIND_KEITHLEY():
    global Keithley
    global KeithleyReadyStatus
    global ResMan

    # Creating a resource manager
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

def THREAD_FIND_MERCURY():
    global Mercury
    global MercuryReadyStatus
    global ResMan

    list_of_instruments = ResMan.list_resources()
    
    for item in list_of_instruments:
        if ("ASRL" in item.upper()):
            try:
                temp = ResMan.open_resource(item)
                if ("MERCURY" in temp.query("*IDN?")):
                    Mercury = temp
                    del temp
                    Mercury.timeout = 60000
                    MercuryReadyStatus.set(True)
                    break
            except visa.VisaIOError:
                pass
    if Mercury:
        print("Found Mercury: ", Mercury.query("*IDN?"))
    else:
        print("Mercury was not found")
        MercuryReadyStatus.set(False)

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
    global Voltage
    global Current
    global delta_time
    print("Processing Results")
    if RAW_DATA:
        # EXTRACTING DATA
        Voltage = [float(item) for item in RAW_DATA.split(",")[0::3]]
        Current = [float(item) for item in RAW_DATA.split(",")[1::3]]
        delta_time = [float(item) for item in RAW_DATA.split(",")[2::3]]
        print("Results are processed")
    FUNC_REDRAW_BUTTON()

def THREAD_DRAW_DATA():
    global ResultCanvas
    global Voltage
    global Current
    global DrawOriginSettings
    global DrawVoltageAxisRangeEntryValue
    global DrawCurrentAxisRangeEntryValue
    
    ResultCanvas.delete(*ResultCanvas.find_withtag("plot"))
    canvas_width = float(ResultCanvas["width"])
    canvas_height = float(ResultCanvas["height"])
    x_origin = canvas_width/2;
    y_origin = canvas_height/2;
    x_range = abs(float(DrawVoltageAxisRangeEntryValue.get()))
    y_range = abs(float(DrawCurrentAxisRangeEntryValue.get()))

    if "N" in DrawOriginSettings.get().upper():
        y_origin -= 240
    elif "S" in DrawOriginSettings.get().upper():
        y_origin += 240

    if "W" in DrawOriginSettings.get().upper():
        x_origin -= 240
    elif "E" in DrawOriginSettings.get().upper():
        x_origin += 240

    ResultCanvas.create_line(10, y_origin, canvas_width-10, y_origin,
                             fill="#010101",
                             tags=("plot", "axis"))

    ResultCanvas.create_line(x_origin, 10, x_origin, canvas_height-10,
                             fill="#010101",
                             tags=("plot", "axis"))

    dx = 0.25 * math.pow( 10, math.floor(math.log10(x_range)) )
    dy = 0.25 * math.pow( 10, math.floor(math.log10(y_range)) )

    for i in range(1, math.floor(x_range/dx)+1):
        ResultCanvas.create_line((dx*i)/x_range*(canvas_width-20)+x_origin, 10, (dx*i)/x_range*(canvas_width-20)+x_origin, canvas_height-10,
                                 fill="#aaaaaa", tags=("plot","axis"))
        ResultCanvas.create_text((dx*i)/x_range*(canvas_width-20)+x_origin, canvas_height-10, anchor=tkinter.NW, text="%2.2e"%(dx*i), tags=("plot", "axis"))
        
        ResultCanvas.create_line(-(dx*i)/x_range*(canvas_width-20)+x_origin, 10, -(dx*i)/x_range*(canvas_width-20)+x_origin, canvas_height-10,
                                 fill="#aaaaaa", tags=("plot","axis"))
        ResultCanvas.create_text(-(dx*i)/x_range*(canvas_width-20)+x_origin, canvas_height-10, anchor=tkinter.NW, text="%2.2e"%(-dx*i), tags=("plot", "axis"))

    for j in range(1, math.floor(y_range/dy)+1):
        ResultCanvas.create_line( 10, -(dy*j)/y_range*(canvas_width-20)+y_origin, canvas_width-10, -(dy*j)/y_range*(canvas_width-20)+y_origin,
                                 fill="#aaaaaa", tags=("plot","axis"))
        ResultCanvas.create_text(10, -(dy*j)/y_range*(canvas_width-20)+y_origin, anchor=tkinter.NW, text="%2.2e"%(dy*j), tags=("plot", "axis"))
        
        ResultCanvas.create_line( 10, (dy*j)/y_range*(canvas_width-20)+y_origin, canvas_width-10, (dy*j)/y_range*(canvas_width-20)+y_origin,
                                 fill="#aaaaaa", tags=("plot","axis"))
        ResultCanvas.create_text(10, (dy*j)/y_range*(canvas_width-20)+y_origin, anchor=tkinter.NW, text="%2.2e"%(-dy*j), tags=("plot", "axis"))

    if Voltage and Current:
        x_points = [v/x_range * (canvas_width-20) + x_origin for v in Voltage]
        y_points = [-i/y_range * (canvas_height-20) + y_origin for i in Current]

        ResultCanvas.create_line(list(zip(x_points, y_points)),
                                 fill="#1010ff", width=2,
                                 tags=("plot"))
        
    
    pass

# THREADS END

# THREADS INI


# THREADS INI END

# FRAMES
StatusFrame = tkinter.LabelFrame(root)
StatusFrame["text"] = "Status"

ControlFrame = tkinter.LabelFrame(root)
ControlFrame["text"] = "Keithley Sweep Control"

ResultFrame = tkinter.LabelFrame(root)
ResultFrame["text"] = "Result"

MercFrame = tkinter.LabelFrame(root)
MercFrame["text"] = "Mercury Control"

SaveFrame = tkinter.LabelFrame(root)
SaveFrame["text"] = "Save data"

StatusFrame.grid(row=0,column=0)
ControlFrame.grid(row=1,column=0)
ResultFrame.grid(row=0,column=1,rowspan=2)
MercFrame.grid(row=0,column=2)
SaveFrame.grid(row=1,column=2)
# FRAMES END

# STATUS FRAME
tkinter.Label(StatusFrame, text="Keithley: ").grid(row=0,column=0)
KeithleyStatusLabel = tkinter.Label(StatusFrame, text="Pending", bg="#ff0000")
KeithleyStatusLabel.grid(row=0,column=1)
KeithleyReadyStatus.trace("w", FUNC_KEITHLEY_STATUS_CHANGE)

tkinter.Label(StatusFrame, text="Mercury: ").grid(row=1,column=0)
MercuryStatusLabel = tkinter.Label(StatusFrame, text="Pending",
                                   bg="#ff0000")
MercuryStatusLabel.grid(row=1,column=1)
MercuryReadyStatus.trace("w", FUNC_MERCURY_STATUS_CHANGE)

RefreshInstrumentsButton = tkinter.Button(StatusFrame, text="Refresh Instruments",
                                          command=FUNC_REFRESH_INST_BUTTON)
RefreshInstrumentsButton.grid(row=2,column=0,columnspan=2)
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
ResultCanvas.grid(row=0,column=0,columnspan=2)

OriginSettingsFrame = tkinter.LabelFrame(ResultFrame, text="Origin")
OriginSettingsFrame.grid(row=1,column=0)

OriginNW = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="NW")
OriginNW.grid(row=0,column=0)

OriginN = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="N")
OriginN.grid(row=0,column=1)

OriginNE = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="NE")
OriginNE.grid(row=0,column=2)

OriginW = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="W")
OriginW.grid(row=1,column=0)

OriginC = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="C")
OriginC.grid(row=1,column=1)

OriginE = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="E")
OriginE.grid(row=1,column=2)

OriginSW = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="SW")
OriginSW.grid(row=2,column=0)

OriginS = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="S")
OriginS.grid(row=2,column=1)

OriginSE = tkinter.Radiobutton(OriginSettingsFrame, variable=DrawOriginSettings,
                              value="SE")
OriginSE.grid(row=2,column=2)

AxisSettingsFrame = tkinter.LabelFrame(ResultFrame, text="Axis")
AxisSettingsFrame.grid(row=1,column=1)

tkinter.Label(AxisSettingsFrame, text="Voltage range: ").grid(row=0,column=0)
DrawVoltageAxisSettingsEntry = tkinter.Entry(AxisSettingsFrame,
                                             textvariable=DrawVoltageAxisRangeEntryValue)
DrawVoltageAxisSettingsEntry.grid(row=0,column=1)

tkinter.Label(AxisSettingsFrame, text="Current range: ").grid(row=1,column=0)
DrawCurrentAxisSettingsEntry = tkinter.Entry(AxisSettingsFrame,
                                             textvariable=DrawCurrentAxisRangeEntryValue)
DrawCurrentAxisSettingsEntry.grid(row=1,column=1)

RedrawButton = tkinter.Button(ResultFrame, text="Redraw",
                              command=FUNC_REDRAW_BUTTON)
RedrawButton.grid(row=2,column=0,columnspan=2)

# RESULT FRAME END

# MERCURY FRAME
# MERCURY FRAME END

# SAVE DATA FRAME
# SAVE DATA FRAME END

# INI AREA
FUNC_REFRESH_INST_BUTTON()

FUNC_REDRAW_BUTTON()

ScanningStatus.trace("w", FUNC_SCANNING_STATUS_CHANGE)

# INI AREA END

# TEST AREA


# TEST AREA END

root.mainloop()
