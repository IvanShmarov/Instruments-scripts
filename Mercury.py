import visa

Mercury = None

ResMan = visa.ResourceManager()

list_of_instruments = ResMan.list_resources()

for item in list_of_instruments:
    if ("ASRL" in item.upper()):
        try:
            temp = ResMan.open_resource(item)
            if ("MERCURY" in temp.query("*IDN?")):
                Mercury = temp
                Mercury.timeout = 60000
                break
        except visa.VisaIOError:
            print("Not a thing")
if Mercury:
    print("Found Mercury: ", Mercury.query("*IDN?"))
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:ENAB:ON"))
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:PIDT:ON"))
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:60"))
else:
    print("Mercury was not found")
    
#SET:DEV:MB1.T1:TEMP:LOOP:ENAB:ON
#SET:DEV:MB1.T1:TEMP:LOOP:PIDT:ON
#SET:DEV:MB1.T1:TEMP:LOOP:TSET:X
#Where X is the temperature
