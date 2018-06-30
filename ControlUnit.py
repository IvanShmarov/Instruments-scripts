import tkinter
import visa
import threading

root = tkinter.Tk()
root.title("Control unit")

# IMPORTANT VARIABLES
KeithleyReadyStatus = tkinter.BooleanVar()
KeithleyReadyStatus.set(False)

StartVoltageEntryValue = tkinter.StringVar()
StartVoltageEntryValue.set("0.0")

EndVoltageEntryValue = tkinter.StringVar()
EndVoltageEntryValue.set("1.0")

TimeIncrementEntryValue = tkinter.StringVar()
TimeIncrementEntryValue.set("10e-3")

BothWayScan = tkinter.BooleanVar()
BothWayScan.set(False)

# IMPORTANT VARIABLES END

# INSTRUMENTS

Keithley = None

Mercury = None

# INSTUMENTS END

# FUNCTIONS
def FUNC_SCAN_BUTTON(*args):
    global Keithley
    global KeithleyReadyStatus
    print(args)
    pass

def FUNC_SWAP_BUTTON(*args):
    global StartVoltageEntryValue
    global EndVoltageEntryValue
    print(args)
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
        KeithleyReadyStatus.set(True)
    else:
        print("Keithley was not found")
        KeithleyReadyStatus.set(False)
        

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
tkinter.Label(StatusFrame, text="Mercury: ").grid(row=1,column=0)

KeithleyStatusLabel = tkinter.Label(StatusFrame, text="Pending", bg="#ff0000")
KeithleyStatusLabel.grid(row=0,column=1)
KeithleyReadyStatus.trace("w", FUNC_KEITHLEY_STATUS_CHANGE)

MercuryStatusLabel = tkinter.Label(StatusFrame, text="Not supported Yet", bg="#ffff00")
MercuryStatusLabel.grid(row=1,column=1)
# STATUS FRAME END

# CONTROL FRAME
tkinter.Label(ControlFrame, text="Start Voltage: ").grid(row=0,column=0)
StartVoltageEntry = tkinter.Entry(ControlFrame, textvariable=StartVoltageEntryValue)
StartVoltageEntry.grid(row=0,column=1)

tkinter.Label(ControlFrame, text="End Voltage: ").grid(row=1,column=0)
EndVoltageEntry = tkinter.Entry(ControlFrame, textvariable=EndVoltageEntryValue)
EndVoltageEntry.grid(row=1,column=1)

SwapButton = tkinter.Button(ControlFrame, text="Swap start and end voltages",
                            command=FUNC_SWAP_BUTTON)
SwapButton["width"] = 25
SwapButton["height"] = 2
SwapButton["bg"] = "#ECF7FF"
SwapButton.grid(row=2,column=0,columnspan=2)

tkinter.Label(ControlFrame, text="Time increment: ").grid(row=3,column=0)
TimeIncrementEntry = tkinter.Entry(ControlFrame, textvariable=TimeIncrementEntryValue)
TimeIncrementEntry.grid(row=3,column=1)

BothWayScanCheckButton = tkinter.Checkbutton(ControlFrame, text="Scan forward and backward",
                                             variable = BothWayScan, offvalue=False,
                                             onvalue=True)
BothWayScanCheckButton.grid(row=4,column=0,columnspan=2)


ScanButton = tkinter.Button(ControlFrame, text="SCAN", command=FUNC_SCAN_BUTTON)
ScanButton["width"] = 25
ScanButton["height"] = 2
ScanButton["bg"] = "#ECF7FF"
ScanButton.grid(row=5,column=0,columnspan=2)
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

# INI AREA END

# TEST AREA


# TEST AREA END

root.mainloop()
