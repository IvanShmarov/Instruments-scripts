import visa
import time
import json
from threading import Thread

# INI


SEQUENCE = []

SourceMeter = None
ResistoMeter = None
LightSource = None
Mercury = None

# FUNCTIONS

def thread_caller(seq):
    print(seq)
    if seq:
        the_thread = Thread(args=(seq[1:],))
        if seq[0] == 1:
            the_thread._target = Func_1
        elif seq[0] == 2:
            the_thread._target = Func_2
        elif seq[0] == 3:
            the_thread._target = Func_3
        else:
            print("INVALID!!!!!!!: ", seq[0])
            the_thread._target = thread_caller
        the_thread.start()
    else:
        print("Done")

def Func_1(seq):
    print("\nStarting function 1")

    data = {"Count": 0,"Voltage":[], "Current":[], "Time":[], "Thermistor":[]}
    
    # Getting parameters from config
    V0 = config["Func 1"]["V0"]
    Light = config["Func 1"]["Light"] * config["LightSource"]["Sun_Current"]
    
    # Setting instruments
    SourceMeter.write("""
TRAC:CLE
SOUR:VOLT %f
OUTP:STAT ON
""" % V0) # Source produces V0 volts and otuput is on
    LightSource.write("CURR %f" % Light ) # Light source is 0 or 1 sun
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:77")) # Set target temp to 77K
    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )

    # Do many measurements
    while chamber_temp > 78.0:
        source_reading = SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")
        therm_reading = ResistoMeter.query("READ?")

        data["Voltage"].append(float( source_reading[0] ))
        data["Current"].append(float( source_reading[1] ))
        data["Time"].append(float( source_reading[2] ))
        data["Thermistor"].append(float( therm_reading ))
        data["Count"] += 1
        print("Func 1 points measured: ", data["Count"])
        
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        time.sleep(0.05)

    # Switch stuff off
    SourceMeter.write("""
SOUR:VOLT 0
OUTP:STAT OFF
""")
    LightSource.write("CURR 0")

    # Save data
    scan_time = time.gmtime()
    record = dict()
    record.update(config["Save Header"])
    record["Type"] = "FUNC 1"
    record["Time"] = time.asctime(scan_time)
    record["Light current"] = Light
    record["data"] = dict()
    record["data"].update( data )
    file_name = config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.gmtime()) + ".txt"
    save_file = open(file_name, "w")
    save_file.write(json.dumps(record))
    save_file.close()

    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 1")

def Func_2(seq):
    print("\nStarting function 2")

    data = {"Count": 0,"Voltage":[], "Current":[], "Time":[], "Thermistor":[]}

    # Getting parameters from config
    temp_start = config["Func 2"]["Temp Start"]
    temp_end = config["Func 2"]["Temp End"]
    temp_step = config["Func 2"]["Temp Step"]
    light_ints = [i * config["LightSource"]["Sun_Current"] for i in config["Func 2"]["Light Ints"]]

    # Do many measurements
    for temp in range(temp_start, temp_end + 1, temp_step):
        # Talk to Mercury
        print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:%f" % temp))
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        while abs(chamber_temp - temp) > 1.5:
            time.sleep(1)
            chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        time.sleep(10)
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 2")

def Func_3(seq):
    print("\nStarting function 3")
    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 3")

# ACTION

rm = visa.ResourceManager()
list_of_instruments = rm.list_resources()



for item in list_of_instruments:
    if "::0x05E6::0x2450::" in item:
        SourceMeter = rm.open_resource(item)
        print("SourceMeter:\t", SourceMeter.query("*IDN?"))
    elif "::0x05E6::0x2110:" in item:
        ResistoMeter = rm.open_resource(item)
        print("ResistoMeter:\t", ResistoMeter.query("*IDN?"))
    elif "::0x05E6::0x2200::" in item:
        LightSource = rm.open_resource(item)
        print("LightSource:\t", LightSource.query("*IDN?"))
    elif "ASRL4" in item:
        Mercury = rm.open_resource(item)
        print("Mercury:\t", Mercury.query("*IDN?"))


if SourceMeter and ResistoMeter and LightSource and Mercury:
    
    config_file = open("cu2_config.txt", "r")
    config = json.loads(config_file.read())
    config_file.close()

    for item in config:
        if item == "SourceMeter":
            SourceMeter.write( config[item]["INI"] % tuple( config[item]["PAR"]  ) )
        elif item == "ResistoMeter":
            ResistoMeter.write( config[item]["INI"] % tuple( config[item]["PAR"]  ) )
        elif item == "LightSource":
            LightSource.write( config[item]["INI"] % tuple( config[item]["PAR"]  ) )
        elif item == "Mercury":
            Mercury.write( config[item]["INI"] % tuple( config[item]["PAR"]  ) )


    print("Everything seems good")
    SEQUENCE = [int(item) for item in input("Enter the sequence:\n").split()]
    thread_caller(SEQUENCE)
