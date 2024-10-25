import omni.ext
import omni.ui as ui
import paho.mqtt.client as mqtt
import carb.events
import json
import os
from omni.kit.app import get_app
import pathlib

# Daisy_DATA = carb.events.type_from_string("ielabs.mqtt.TM_12_POS.Daisy")
EXT_DATA_PATH = pathlib.PurePath(__file__).parents[3] / "data" / "ext_data.json"
Rosie_DATA = carb.events.type_from_string("ielabs.mqtt.TM_12_POS.Rosie")
bus = get_app().get_message_bus_event_stream()

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class Paho_mqttExtension(omni.ext.IExt):

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.combo: ui.ComboBox
        self.topic_event_type_ui_elements = []
        self.types = ["int", "float", "string", "array<int>", "array<float>", "array<string>"]
        self.field_container: ui.VStack
        self.topic_count = 0
        self.no_topics_button: ui.Button

    def topic_fields(self):
        with self.field_container:
            field_set = ui.HStack()
            with field_set:
                ui.Label("MQTT Topic", height = 20, width = 70)
                topic_field = ui.StringField(height = 20, width = 200)
                ui.Separator(height = 10)
                ui.Label("Custom Event topic", height = 20, width = 100)
                custom_event_field = ui.StringField(height = 20, width = 200)
                ui.Separator(height = 10)
                ui.Label("Data Type", height = 20, width = 50)
                combo = ui.ComboBox(0, *self.types)

                elements = (topic_field, custom_event_field, combo)
                self.topic_event_type_ui_elements.append(elements)                    
                ui.Button("Add", width=20, height=20, clicked_fn=self.topic_fields)
                def remove_fields():
                    try:
                        self.topic_event_type_ui_elements.remove(elements)
                    except ValueError as e:
                        print("error, couldn't find ui elements")
                    field_set.visible = False
                    self.topic_count -= 1
                    print(self.get_values_from_topics_ui())
                    if self.topic_count == 0:
                        self.no_topics_button.visible = True
                ui.Button("Remove", width=20, height=20, clicked_fn=remove_fields)
                self.topic_count += 1

    def no_topics_add_button(self):
        def add_and_hide():
            self.topic_fields()
            self.no_topics_button.visible = False
        self.no_topics_button = ui.Button("Add Topic", width=20, height=20, clicked_fn=add_and_hide)
    
    def on_startup(self, ext_id):
        # self.host_ip = "192.168.4.128"
        # self.port = 8882
        # self.user = "omni_user"
        # self.password = "Omniverse@123"
        # self.ca_crt = r"C:\Users\iescale16\Documents\Kit\apps\exttest_ielabs_mqtt_addition\exts\paho_mqtt\data\ca.crt"
        # self.mqtt_topic = "Daisy_Joint_Positions"
        # self.custom_event = "ielabs.mqtt.TM_12_POS.Daisy"
        self.topic_count = 0

        def label_create_v(name,psw=False):    
            ui.Label(name, height = 20)
            value = ui.StringField(height =20, password_mode = psw)
            ui.Separator(height = 10)
            return value
        
        print("[paho_mqtt] paho_mqtt startup")
        self._count = 0
        self._window = ui.Window("MQTT Broker details")
        with self._window.frame:
            with ui.VStack():
                with ui.CollapsableFrame("Connection details"):
                    with ui.VStack():
                        self.broker_name_field = label_create_v("Broker Name")
                        self.host_ip_field = label_create_v("IP Address")
                        self.port_field = label_create_v("Port")
                        self.user_field = label_create_v("User Name")  
                        self.password_field = label_create_v("Password",False)
                        self.ca_crt_field = label_create_v("CA Certificate path (for TLS)")
                        self.no_topics_add_button()
                with ui.CollapsableFrame("Topics"):
                    self.field_container = ui.VStack()
                    with self.field_container:
                        self.topic_fields()
                ui.Button("Execute",height=20, clicked_fn=self.run_program)
                ui.Separator(height = 20)
                ui.Button("Save Details",height=20, clicked_fn=self.save_button)
                ui.Separator(height = 20)
                ui.Button("Load Previous Details",height=20, clicked_fn=self.initialize_ui)
                 
    def save_ext_data(self):
        print(f"file path to save: {EXT_DATA_PATH}")
        os.makedirs(os.path.dirname(EXT_DATA_PATH), exist_ok=True)
        data = {
            "broker_name":self.broker_name,
            "host_ip":self.host_ip,
            "port":self.port,
            "user":self.user,
            "password":self.password,
            "ca_crt":self.ca_crt,
            "topics":self.get_values_from_topics_ui()
        }
        try:
            with open(EXT_DATA_PATH,"w") as json_file:
                json.dump(data, json_file)
            print("Saved data successfully")
        except FileNotFoundError:
            print("File not saved")    
            
    def load_ext_data(self):
        try:
            with open(EXT_DATA_PATH,"r") as json_file:
                data = json.load(json_file)
                return data
        except FileNotFoundError:
            print("No saved data found.")
            return {
                "broker_name":"",
                "host_ip":"",
                "port":"",
                "user":"",
                "password":"",
                "ca_crt":"",
                "topics":"",
            }
    
    def get_values_from_topics_ui(self):
        topics_events_types = []
        for topic, event, type in self.topic_event_type_ui_elements:
            to = topic.model.get_value_as_string()
            e = event.model.get_value_as_string()
            ty = type.model.get_item_value_model().get_value_as_int()
            topics_events_types.append((to, e, ty))
        return topics_events_types

    def initialize_ui(self):
        data = self.load_ext_data()
        self.broker_name_field.model.set_value(data.get("broker_name","")) 
        self.host_ip_field.model.set_value(data.get("host_ip",""))
        self.port_field.model.set_value(data.get("port",""))
        self.user_field.model.set_value(data.get("user",""))
        self.password_field.model.set_value(data.get("password",""))
        self.ca_crt_field.model.set_value(data.get("ca_crt",""))
        topics: list = list(data.get("topics", []))
        print(f"topics saved: {topics}")
        print(f"topic count: {self.topic_count}")
        for _ in range(len(topics) - self.topic_count):
           self.topic_fields() 
        print(f"topic count: {self.topic_count}")

        for (topic, event, type), (topic_ui, event_ui, type_ui) in zip(topics, self.topic_event_type_ui_elements):
            topic_ui.model.set_value(topic)
            event_ui.model.set_value(event)
            type_ui.model.get_item_value_model().set_value(type)
        print("Loaded into UI")
        
    def save_button(self):
        self.broker_name = self.broker_name_field.model.get_value_as_string()
        self.host_ip = self.host_ip_field.model.get_value_as_string()
        self.port = int(self.port_field.model.get_value_as_string())
        self.user = self.user_field.model.get_value_as_string()      
        self.password = self.password_field.model.get_value_as_string()
        self.ca_crt = self.ca_crt_field.model.get_value_as_string()
        self.save_ext_data()
        
    def run_program(self): # Collect values from the input fields
        self.broker_name = self.broker_name_field.model.get_value_as_string()
        self.host_ip = self.host_ip_field.model.get_value_as_string()
        self.port = int(self.port_field.model.get_value_as_string())
        self.user = self.user_field.model.get_value_as_string()      
        self.password = self.password_field.model.get_value_as_string()
        self.ca_crt = self.ca_crt_field.model.get_value_as_string()

        self.topic_event_type = []
        for topic, event, type in self.topic_event_type_ui_elements:
            topic = topic.model.get_value_as_string()
            event = event.model.get_value_as_string()
            type = self.types[type.model.get_item_value_model().get_value_as_int()]
            self.topic_event_type.append((topic, event, type))
        
        try:
            self.client.connect(self.host_ip, self.port)
            self.client.username_pw_set(self.user, self.password)
            self.client.tls_set(ca_certs=self.ca_crt)
            self.client.loop_start()
        except Exception as e: 
            print(f"Not connected {e}")
        
    def on_shutdown(self):
        print("[ielabs.mqtt.test] ielabs mqtt test shutdownc")
        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        for topic, _, _ in self.topic_event_type:
            self.client.subscribe(topic)

    def decode(self, message: str, type: str):
        result = None
        print(f"decoding {message} with type {type}")
        match type:
            case "int":
                result = int(message)
            case "float":
                result = float(message)
            case "string":
                result = message
            case "array<int>":
                result = list(map(int, list(json.loads(message))))
            case "array<float>":
                result = list(map(float, list(json.loads(message))))
            case "array<string>":
                result = list(map(str, list(json.loads(message))))
        return result

    def on_message(self, client, userdata, msg):
        for value in self.topic_event_type:
            if value[0] != msg.topic: 
                continue
            topic, event, type = value
            message_str = msg.payload.decode("utf-8")
            try:
                message = self.decode(message_str, type)
                print(f"sending message {message} on bus {event}")
                event_type = carb.events.type_from_string(event)
                bus.push(event_type, payload={"msg": message})
                topic = "Status_v2"
                self.client.publish(topic,self.broker_name)
            except ValueError as e:
                print(f"Failed to convert input {message_str} to type {type}: {e}")
                