import visa

rm = visa.ResourceManager()
addr = [i for i in rm.list_resources() if "0x2110" in i][0]

resist = rm.open_resource(addr)
print(resist.query("*IDN?"),resist.query("CONF?"))

resist.write("CONF:FRES 1e3")
print(resist.query("CONF?"))
print(resist.query("READ?"))
