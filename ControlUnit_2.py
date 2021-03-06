kek = "kek is always defined, kek"
import visa
import time
import json
import matplotlib.pyplot as plt
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
        elif seq[0] == 4:
            the_thread._target = Func_4
        elif seq[0] == 5:
            the_thread._target = Func_5
        else:
            print("INVALID!!!!!!!: ", seq[0])
            the_thread._target = thread_caller
        the_thread.start()
    else:
        print("Done\n")
        SourceMeter.write("""
OUTP:STATE OFF
""")
        LightSource.write("OUTP OFF")
        input("Input enything to finish the program\n")
        plt.close("all")
        

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
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:10")) # Set target temp to 77K
    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )

    # Do many measurements
    while chamber_temp > 80.0:
        source_reading = SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")
        therm_reading = ResistoMeter.query("READ?")

        data["Voltage"].append(float( source_reading[0] ))
        data["Current"].append(float( source_reading[1] ))
        data["Time"].append(float( source_reading[2] ))
        data["Thermistor"].append(float( therm_reading ))
        data["Count"] += 1
        print("Func 1 points measured: ", data["Count"])
        
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        print("The temperature is: ", chamber_temp)
        time.sleep(0.1)
        
    scan_time = time.localtime()
    # Switch stuff off
    SourceMeter.write("""
SOUR:VOLT 0
OUTP:STAT OFF
""")
    LightSource.write("CURR 0")

    # Save data
    
    record = dict()
    record.update(config["Save Header"])
    record["Type"] = "FUNC 1"
    record["Params"] = dict()
    record["Params"].update(config["Func 1"])
    record["Time"] = time.asctime(scan_time)
    record["Light current"] = Light
    record["data"] = dict()
    record["data"].update( data )
    file_name = "F1_"+config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
    save_file = open(file_name, "w")
    save_file.write(json.dumps(record, indent=4))
    save_file.close()
    
    plt.close("all")
##    temp_plot = plt.figure("FUNC 1, Voltage:%f, Light:%f" % (V0, Light))
##    plt.subplot(221)
##    plt.title("Therm vs. Time")
##    plt.plot(data["Time"], data["Thermistor"])
##    plt.subplot(222)
##    plt.title("Cur vs. Time")
##    plt.plot(data["Time"], data["Current"])
##    plt.subplot(223)
##    plt.title("Cur vs. Therm")
##    plt.plot(data["Thermistor"], data["Current"])
##    plt.pause(0.05)
##    temp_plot.show()

    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 1")

def Func_2(seq):
    print("\nStarting function 2")

    data = {"Count": 0,"Voltage":[], "Current":[], "Time":[], "Thermistor":{}}
    raw_data_1 = ""
    raw_data_2 = ""

    # Getting parameters from config
    temp_start = config["Func 2"]["Temp Start"]
    temp_end = config["Func 2"]["Temp End"]
    temp_step = config["Func 2"]["Temp Step"]
    light_ints = [i * config["LightSource"]["Sun_Current"] for i in config["Func 2"]["Light Ints"]]
    V0 = config["Func 2"]["V0"]
    V1 = config["Func 2"]["V1"]
    num = config["Func 2"]["Num"]
    both_ways = config["Func 2"]["Both_ways"]
    delay = config["Func 2"]["delay"]

    # Do many measurements
    for temp in range(temp_start, temp_end + 1, temp_step):
        print("Now aiming for temperature %fK" % temp)
        # Talk to Mercury
        print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:%f" % temp))
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        while abs(chamber_temp - temp) > 1.5:
            time.sleep(1)
            chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        time.sleep(10)
        for intens in light_ints:
            print("Light current is %f" % intens)
            LightSource.write("CURR %f" % intens)
            start_therm_1 = float( ResistoMeter.query("READ?") )
            SourceMeter.write("""
TRAC:CLE "defbuffer1"
SOUR:SWE:VOLT:LIN %f, %f, %f, %f, 1, BEST, OFF, OFF, "defbuffer1"
INIT
*WAI
""" % (V0, V1, num, delay))
            raw_data_1 = SourceMeter.query('TRAC:DATA? 1, %f, "defbuffer1", SOUR, READ, REL' % num)
            end_therm_1 = float( ResistoMeter.query("READ?") )
            scan_time_1 = time.localtime()

            if both_ways:
                start_therm_2 = float( ResistoMeter.query("READ?") )
                SourceMeter.write("""
TRAC:CLE "defbuffer2"
SOUR:SWE:VOLT:LIN %f, %f, %f, %f, 1, BEST, OFF, OFF, "defbuffer2"
INIT
*WAI
""" % (V1, V0, num, delay))
                raw_data_2 = SourceMeter.query('TRAC:DATA? 1, %f, "defbuffer2", SOUR, READ, REL' % num)
                end_therm_2 = float( ResistoMeter.query("READ?") )
                scan_time_2 = time.localtime()

            SourceMeter.write("""
SOUR:VOLT 0
OUTP:STAT OFF
""")
            raw_data_1 = raw_data_1.split(",")
            data["Count"] = num
            data["Voltage"] = [float(item) for item in raw_data_1[0::3]]
            data["Current"] = [float(item) for item in raw_data_1[1::3]]
            data["Time"] = [float(item) for item in raw_data_1[2::3]]
            data["Thermistor"] = (start_therm_1, end_therm_1)

            # Save file
            record = dict()
            record.update(config["Save Header"])
            record["Type"] = "FUNC 2 V0->V1"
            record["Params"] = dict()
            record["Params"].update(config["Func 2"])
            record["Time"] = time.asctime(scan_time_1)
            record["Light current"] = intens
            record["data"] = dict()
            record["data"].update( data )
            file_name = "F2_" + config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
            save_file = open(file_name, "w")
            save_file.write(json.dumps(record, indent=4))
            save_file.close()
            

            plt.close("all")
##            temp_plot_1 = plt.figure("FUNC 2, Temp: %f, Volt: %f->%f, Light: %f" % (temp, V0, V1, intens))
##            plt.subplot(221)
##            plt.title("Cur vs. Time")
##            plt.plot(data["Time"], data["Current"])
##            plt.subplot(222)
##            plt.title("V vs. Time")
##            plt.plot(data["Time"], data["Voltage"])
##            plt.subplot(223)
##            plt.title("I vs. V")
##            plt.plot(data["Voltage"], data["Current"])
##            plt.pause(0.05)
##            temp_plot_1.show()
            
            if both_ways:
                raw_data_2 = raw_data_2.split(",")
                data["Count"] = num
                data["Voltage"] = [float(item) for item in raw_data_2[0::3]]
                data["Current"] = [float(item) for item in raw_data_2[1::3]]
                data["Time"] = [float(item) for item in raw_data_2[2::3]]
                data["Thermistor"] = (start_therm_2, end_therm_2)
                
                record = dict()
                record.update(config["Save Header"])
                record["Type"] = "FUNC 2 V1->V0"
                record["Params"] = dict()
                record["Params"].update(config["Func 2"])
                record["Time"] = time.asctime(scan_time_2)
                record["Light current"] = intens
                record["data"] = dict()
                record["data"].update( data )
                file_name = "F2_"+config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
                save_file = open(file_name, "w")
                save_file.write(json.dumps(record, indent=4))
                save_file.close()
                
                plt.close("all")
##                temp_plot_2 = plt.figure("FUNC 2, Temp: %f, Volt: %f->%f, Light: %f" % (temp, V1, V0, intens))
##                plt.subplot(221)
##                plt.title("Cur vs. Time")
##                plt.plot(data["Time"], data["Current"])
##                plt.subplot(222)
##                plt.title("V vs. Time")
##                plt.plot(data["Time"], data["Voltage"])
##                plt.subplot(223)
##                plt.title("I vs. V")
##                plt.plot(data["Voltage"], data["Current"])
##                plt.pause(0.05)
##                temp_plot_2.show()

        LightSource.write("CURR 0")
    # Switch stuff off
    SourceMeter.write("""
SOUR:VOLT 0
OUTP:STAT OFF
""")
    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 2")

def Func_3(seq):
    print("\nStarting function 3")

    

    V0 = config["Func 3"]["V0"]
    duration = config["Func 3"]["Time"]
    light_ints = [0, config["LightSource"]["Sun_Current"]]

    for intens in light_ints:
        data = {"Count": 0,"Voltage":[], "Current":[], "Time":[], "Thermistor":[]}
        LightSource.write("CURR %f" % intens)
        SourceMeter.write("""
TRAC:CLE "defbuffer1"
SOUR:VOLT %f
OUTP:STAT ON
""" % V0)

    

        start_time = time.time()

        while abs(time.time() - start_time) < duration:
            source_reading = SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")
            therm_reading = ResistoMeter.query("READ?")

            data["Voltage"].append(float( source_reading[0] ))
            data["Current"].append(float( source_reading[1] ))
            data["Time"].append(float( source_reading[2] ))
            data["Thermistor"].append(float( therm_reading ))
            data["Count"] += 1
            print("Func 3 points measured: ", data["Count"], " ", time.time() - start_time)
            time.sleep(0.001)

        SourceMeter.write("""
SOUR:VOLT 0
OUTP:STAT ON
""")

        start_time = time.time()

        while abs(time.time() - start_time) < duration:
            source_reading = SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")
            therm_reading = ResistoMeter.query("READ?")

            data["Voltage"].append(float( source_reading[0] ))
            data["Current"].append(float( source_reading[1] ))
            data["Time"].append(float( source_reading[2] ))
            data["Thermistor"].append(float( therm_reading ))
            data["Count"] += 1
            print("Func 3 points measured: ", data["Count"], " ", time.time() - start_time)
            time.sleep(0.01)

        scan_time = time.localtime()
        # Save data
        record = dict()
        record.update(config["Save Header"])
        record["Type"] = "FUNC 3"
        record["Params"] = dict()
        record["Params"].update(config["Func 3"])
        record["Time"] = time.asctime(scan_time)
        record["Light current"] = intens
        record["data"] = dict()
        record["data"].update( data )
        file_name = "F3_"+config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
        save_file = open(file_name, "w")
        save_file.write(json.dumps(record, indent=4))
        save_file.close()

        plt.close("all")
        temp_plot = plt.figure("FUNC 3, Volt: %f, Duration: %f, Light: %f" % (V0, duration, intens))
        plt.subplot(221)
        plt.title("Therm vs. Time")
        plt.plot(data["Time"], data["Thermistor"])
        plt.subplot(222)
        plt.title("V vs. Time")
        plt.plot(data["Time"], data["Voltage"])
        plt.subplot(223)
        plt.title("Cur vs. Time")
        plt.plot(data["Time"], data["Current"])
        plt.pause(0.05)
        temp_plot.show()

    SourceMeter.write("OUTP:STAT OFF")

    LightSource.write("CURR 0")    
    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 3")

def Func_4(seq):
    print("\nStarting function 4")
    for v in [i * 0.05 for i in range(31)]:
        print("Doing for voltage %f" % v)
        data = {"Count": 0,"Voltage":[], "Current":[], "Time":[], "Thermistor":[]}

        # Cool down with 1.5 V
        SourceMeter.write("""
    TRAC:CLE
    SOUR:VOLT %.3f
    OUTP:STAT ON
    """ % v)

    ##    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:190"))
    ##    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    ##    while abs(chamber_temp - 190) > 1.5:
    ##        time.sleep(1)
    ##        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    ##        print("Cooling down\n")
    ##        print(SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")[0])
        start_time = time.clock()
        while time.clock() - start_time < 600:
            time.sleep(0.5)
            print(SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")[0])
        # Warm up with 0V
        SourceMeter.write("""
    TRAC:CLE
    SOUR:VOLT 0
    OUTP:STAT ON
    """)
    ##    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:225"))
    ##    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    ##    while abs(chamber_temp - 225) > 1.5:
    ##        time.sleep(1)
    ##        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    ##        print("Warming up\n")
    ##        print(SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")[0])
        # Set the light source and measure current with time
        LightSource.write("CURR %f" % (config["LightSource"]["Sun_Current"] * 0.005))
        start_time = time.clock()
        while time.clock() - start_time < 1200:
            source_reading = SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")
            therm_reading = ResistoMeter.query("READ?")
            
            data["Voltage"].append(float( source_reading[0] ))
            data["Current"].append(float( source_reading[1] ))
            data["Time"].append(float( source_reading[2] ))
            data["Thermistor"].append(float( therm_reading ))
            data["Count"] += 1
            print("Func 4 points measured: ", data["Count"])

            time.sleep(0.1)

        scan_time = time.localtime()
        LightSource.write("CURR 0" )

        record = dict()
        record.update(config["Save Header"])
        record["Type"] = "FUNC 4"
        record["Time"] = time.asctime(scan_time)
        record["Light current"] = config["LightSource"]["Sun_Current"] * 0.005
        record["data"] = dict()
        record["data"].update( data )
        file_name = "F4_" + ("%.2f" % v) + "V_" + config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
        save_file = open(file_name, "w")
        save_file.write(json.dumps(record, indent=4))
        save_file.close()

        LightSource.write("CURR %f" % 0)

    LightSource.write("OUTP OFF")
    SourceMeter.write("OUTP:STAT OFF")
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 4")


def Func_5(seq):
    print("\nStarting function 5")
    
    # STEP 1 1.5 V to 190 K
    SourceMeter.write("""
TRAC:CLE
SOUR:VOLT %.3f
OUTP:STAT ON
""")
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:190"))
    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    while abs(chamber_temp - 190) > 1.5:
        time.sleep(1)
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        print("Cooling down\n")
        print(SourceMeter.query("READ? \"defbuffer1\", SOUR, READ, REL").split(",")[0])
    # __________________________________________________________________________________________

    # LOOP
    for i in range(5):
        # STEP 2
        data = {"Count": 0,"Voltage":[], "Current":[], "Time":[]}
        raw_data_1 = ""
        raw_data_2 = ""
        # Forward
        SourceMeter.write("""
TRAC:CLE "defbuffer1"
SOUR:SWE:VOLT:LIN 0, 1.5, 101, 0.01, 1, BEST, OFF, OFF, "defbuffer1"
INIT
*WAI
""" )
        raw_data_1 = SourceMeter.query('TRAC:DATA? 1, 101, "defbuffer1", SOUR, READ, REL')
        scan_time_1 = time.localtime()
        # Backward
        SourceMeter.write("""
TRAC:CLE "defbuffer1"
SOUR:SWE:VOLT:LIN 1.5, 0, 101, 0.01, 1, BEST, OFF, OFF, "defbuffer1"
INIT
*WAI
""" )
        raw_data_2 = SourceMeter.query('TRAC:DATA? 1, 101, "defbuffer1", SOUR, READ, REL')
        scan_time_2 = time.localtime()

        # Saving
        data["Count"] = 101
        data["Voltage"] = [float(item) for item in raw_data_1[0::3]]
        data["Current"] = [float(item) for item in raw_data_1[1::3]]
        data["Time"] = [float(item) for item in raw_data_1[2::3]]

        record = dict()
        record.update(config["Save Header"])
        record["Type"] = "FUNC 5 V0->V1"
        record["Time"] = time.asctime(scan_time_1)
        record["Light current"] = intens
        record["data"] = dict()
        record["data"].update( data )
        file_name = "F5 _1F_" + config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
        save_file = open(file_name, "w")
        save_file.write(json.dumps(record, indent=4))
        save_file.close()

        data["Count"] = 101
        data["Voltage"] = [float(item) for item in raw_data_2[0::3]]
        data["Current"] = [float(item) for item in raw_data_2[1::3]]
        data["Time"] = [float(item) for item in raw_data_2[2::3]]

        record = dict()
        record.update(config["Save Header"])
        record["Type"] = "FUNC 5 V1->V0"
        record["Time"] = time.asctime(scan_time_2)
        record["Light current"] = intens
        record["data"] = dict()
        record["data"].update( data )
        file_name = "F5 _1B_" + config["Save Header"]["Label"] + "_" + time.strftime("[%d_%m]_(%H_%M_%S)", time.localtime()) + ".txt"
        save_file = open(file_name, "w")
        save_file.write(json.dumps(record, indent=4))
        save_file.close()

    
    # Call next function
    print("Func caller")
    thread_caller(seq)
    print("\nEnding function 5")

# ACTION

rm = visa.ResourceManager()
list_of_instruments = rm.list_resources()



for item in list_of_instruments:
    if "::0x05E6::0x2450::" in item:
        SourceMeter = rm.open_resource(item)
        SourceMeter.timeout = 60000
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
            print(Mercury.query( config[item]["INI"] % tuple( config[item]["PAR"]  ) ))
            print(Mercury.read())
            print(Mercury.read())


    print("Everything seems good")
    SEQUENCE = [int(item) for item in input("Enter the sequence:\n").split()]
    thread_caller(SEQUENCE)
