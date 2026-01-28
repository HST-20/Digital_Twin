from opcua import Client, ua
import paho.mqtt.client as mqtt
import numpy as np
import time


client = Client("opc.tcp://192.168.100.0:4840")
client.set_user("ADMIN")
client.set_password("ADMIN123")
client.session_timeout = 3000


broker_address = "127.0.0.1"
port = 1883
client_to_node_red = mqtt.Client()
client_to_node_red.connect(broker_address, port)


node_ids = [
    "ns=2;s=/Plc/DB190.DBD72:REAL",
    "ns=2;s=/Plc/DB190.DBD76:REAL",
    "ns=2;s=/Plc/DB190.DBD80:REAL",
    "ns=2;s=/Plc/DB190.DBD84:REAL",
    "ns=2;s=/Plc/DB190.DBD88:REAL",
    "ns=2;s=/Plc/DB190.DBD92:REAL",
    "ns=2;s=/Plc/DB190.DBD24:REAL",
    "ns=2;s=/Plc/DB190.DBD28:REAL",
    "ns=2;s=/Plc/DB190.DBD32:REAL",
    "ns=2;s=/Plc/DB190.DBD36:REAL",
    "ns=2;s=/Plc/DB190.DBD40:REAL",
    "ns=2;s=/Plc/DB190.DBD44:REAL",
    "ns=2;s=/Nck/MachineAxis/measPos1[2]",
    "ns=2;s=/Channel/ProgramInfo/progName",
    "ns=2;s=/Bag/State/opMode",
    "ns=2;s=/Nck/TopPrioAlarm/clearInfo",
    "ns=2;s=/Nck/TopPrioAlarm/textIndex",
    "ns=2;s=/Channel/ProgramInfo/actLineNumber",
    "ns=2;s=/Channel/State/feedRateIpoOvr",
    "ns=2;s=/Channel/Spindle/speedOvr",
    "ns=2;s=/Channel/State/acPRTimeA",
    "ns=2;s=/Channel/State/acPRTimeB",
    "ns=2;s=/Channel/State/acPRTimeM",
    "ns=2;s=/Channel/State/progStatus",
    "ns=2;s=/Channel/ChannelDiagnose/cycleTime",
    "ns=2;s=/Channel/ProgramInfo/actBlock",
]

class SubHandler(object):
    def __init__(self):
        self.last_values = {}

    def datachange_notification(self, node, val, data):
        topic = node.nodeid.to_string()

        # Only process when the value is a string (since G-code lines are strings)
        if isinstance(val, str):
            val_str = val.strip()

            # Match exactly "G01 Y700.0" or "G01 Y0.0"
            if val_str.startswith("G01 Y"):
                try:
                    # Extract numeric value after 'Y'
                    y_value = float(val_str.split("Y")[1])
                    # Only consider Y700.0 or Y0.0
                    if y_value in (700.0, 0.0):
                        if self.last_values.get(topic) != y_value:
                            self.last_values[topic] = y_value
                            print(f"Extracted Y value: {y_value}")
                            client_to_node_red.publish(topic, str(y_value))
                except ValueError:
                    pass  # Skip lines that aren't properly formatted

        elif isinstance(val, (float, int)):
            val = np.around(val, 3)
            if self.last_values.get(topic) != val:
                self.last_values[topic] = val
                client_to_node_red.publish(topic, str(val))
                print(f"{topic}: {val}")

try:
    client.connect()
    print("Connected to OPC UA")

    handler = SubHandler()
    sub = client.create_subscription(10, handler)
    for nid in node_ids:
        node = client.get_node(nid)
        sub.subscribe_data_change(node)


    while True:
        time.sleep(1)

finally:
    client.disconnect()
    client_to_node_red.disconnect()


