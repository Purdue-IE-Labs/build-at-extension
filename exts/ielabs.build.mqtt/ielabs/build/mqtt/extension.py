import paho.mqtt
import paho.mqtt.client
import omni.ext
import omni.ui as ui
import paho
import paho.mqtt.client as mqtt
import carb.events
import json
import os
from omni.kit.app import get_app
import pathlib
from enum import Enum


class Type(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    ARRAY_INT = "array<int>"
    ARRAY_FLOAT = "array<float>"
    ARRAY_STRING = "array<string>"
    ARRAY_BOOL = "array<bool>"

# Daisy_DATA = carb.events.type_from_string("ielabs.mqtt.TM_12_POS.Daisy")
EXT_DATA_PATH = pathlib.PurePath(__file__).parents[3] / "data" / "ext_data.json"
bus = get_app().get_message_bus_event_stream()

error_styles = { "color": "red", "font_size": 20.0 }
info_styles = { "color": "white", "font_size": 20.0 }

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
        self.client.on_disconnect = self.on_disconnect
        self.client.on_connect_fail = self.on_connect_fail
        self.combo: ui.ComboBox
        self.topic_event_type_ui_elements = []
        self.field_container: ui.VStack
        self.topic_count = 0
        self.no_topics_button: ui.Button
        self.status_label: ui.Label
        self.connect_button: ui.Button

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
                combo = ui.ComboBox(0, *[x.value for x in Type], width = 90)

                ui.Separator(height = 10)
                elements = (topic_field, custom_event_field, combo)
                self.topic_event_type_ui_elements.append(elements)                    
                ui.Button("Add", width=20, height=20, clicked_fn=self.topic_fields)
                def remove_fields():
                    try:
                        self.topic_event_type_ui_elements.remove(elements)
                    except ValueError as e:
                        pass
                    field_set.visible = False
                    self.topic_count -= 1
                    if self.topic_count == 0:
                        self.no_topics_button.visible = True
                ui.Button("Remove", width=20, height=20, clicked_fn=remove_fields)
                self.topic_count += 1

    def no_topics_add_button(self):
        def add_and_hide():
            self.topic_fields()
            self.no_topics_button.visible = False
        self.no_topics_button = ui.Button("Add Topic", width=20, height=20, clicked_fn=add_and_hide)
        self.no_topics_button.visible = False
    
    def on_startup(self, ext_id):
        self.topic_count = 0

        def label_create_v(name,psw=False):    
            ui.Label(name, height = 20)
            value = ui.StringField(height = 20, password_mode = psw)
            ui.Separator(height = 10)
            return value
        
        self._count = 0
        self._window = ui.Window("MQTT Broker details", width = 1100, height = 800)
        with self._window.frame:
            with ui.VStack():
                with ui.CollapsableFrame("Connection details"):
                    with ui.VStack():
                        self.broker_name_field = label_create_v("Broker Name")
                        self.host_ip_field = label_create_v("IP Address *")
                        self.port_field = label_create_v("Port *")
                        self.user_field = label_create_v("User Name")  
                        self.password_field = label_create_v("Password", True)
                        self.ca_crt_field = label_create_v("CA Certificate path (for TLS)")
                        self.ca_crt_checked = ui.CheckBox(margin = 0)
                        self.ca_crt_checked.model.set_value(True)
                        def checked(value: ui.AbstractValueModel):
                            self.ca_crt_field.visible = value.get_value_as_bool()
                        self.ca_crt_checked.model.add_value_changed_fn(checked)
                        self.status_label = ui.Label("", visible=False, height = 70)
                        self.status_label.set_style({ "color": "red", "font_size": 20.0 })
                        self.no_topics_add_button()
                with ui.CollapsableFrame("Topics"):
                    self.field_container = ui.VStack()
                    with self.field_container:
                        self.topic_fields()
                self.connect_button = ui.Button("Connect", height=50, clicked_fn=self.run_program)
                ui.Separator(height = 10)
                ui.Button("Save Details",height=50, clicked_fn=self.save_button)
                ui.Separator(height = 10)
                ui.Button("Load Previous Details",height=50, clicked_fn=self.initialize_ui)
                 
    def save_ext_data(self):
        os.makedirs(os.path.dirname(EXT_DATA_PATH), exist_ok=True)
        topics = [(x[0], x[1], x[2].value) for x in self.get_topics_details()]
        data = {
            "broker_name":self.broker_name,
            "host_ip":self.host_ip,
            "port":self.port,
            "user":self.user,
            "password":self.password,
            "ca_crt":self.ca_crt,
            "topics": topics
        }
        with open(EXT_DATA_PATH,"w") as json_file:
            json.dump(data, json_file)
            
    def load_ext_data(self):
        default_data = {
                "broker_name":"",
                "host_ip":"",
                "port":"",
                "user":"",
                "password":"",
                "ca_crt":"",
                "topics":"",
            }
        if not pathlib.Path(EXT_DATA_PATH).is_file():
            return default_data
        data: dict
        try:
            with open(EXT_DATA_PATH,"r") as json_file:
                data = json.load(json_file)
        except json.JSONDecodeError as e:
            return default_data
        return data
    
    def get_topics_details(self):
        self.update_status()
        error_message = ""
        topics_events_types = []
        for topic, event, type in self.topic_event_type_ui_elements:
            to = topic.model.get_value_as_string()
            e = event.model.get_value_as_string()
            if len(to) == 0 or len(e) == 0:
                error_message = "Must provide non-empty topic and event\n"
                self.update_status(error_message)
                return []
            ty = list(Type)[type.model.get_item_value_model().get_value_as_int()]
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
        self.ca_crt_checked.model.set_value(bool(len(data.get("ca_crt", ""))))
        topics: list = list(data.get("topics", []))
        for _ in range(len(topics) - self.topic_count):
           self.topic_fields() 
        self.no_topics_button.visible = not bool(self.topic_count)

        for (topic, event, type), (topic_ui, event_ui, type_ui) in zip(topics, self.topic_event_type_ui_elements):
            topic_ui.model.set_value(topic)
            event_ui.model.set_value(event)
            type_ui.model.get_item_value_model().set_value(list(Type).index(Type(type)))
    
    def get_connection_details(self):
        self.update_status()
        error_message = ""

        self.broker_name = self.broker_name_field.model.get_value_as_string()
        self.host_ip = self.host_ip_field.model.get_value_as_string()
        if len(self.host_ip) == 0:
            error_message = "IP Address required\n"
        try:
            self.port = int(self.port_field.model.get_value_as_string())
        except ValueError as e:
            error_message += "Port could not be converted to integer\n"
        self.user = self.user_field.model.get_value_as_string() 
        self.password = self.password_field.model.get_value_as_string()
        self.ca_crt = self.ca_crt_field.model.get_value_as_string()

        self.update_status(error_message)
        return len(error_message) == 0
        
    def save_button(self):
        if self.get_connection_details():
            self.save_ext_data()
        
    def run_program(self): # Collect values from the input fields
        if self.client.is_connected():
            self.client.disconnect()

        if not self.get_connection_details() or not self.get_topics_details():
            return
        
        try:
            if len(self.user) and len(self.password):
                self.client.username_pw_set(self.user, self.password)
            if len(self.ca_crt):
                self.client.tls_set(ca_certs=self.ca_crt)
            self.client.connect(self.host_ip, self.port)
            self.client.loop_start()
        except Exception as e: 
            self.update_status(f"Failed to connect to broker, error: {e}")
        
    def on_shutdown(self):
        self.client.loop_stop()
    
    def disconnect(self):
        self.client.disconnect()

    def on_connect_fail(self, client, userdata):
        self.update_status(f"Client failed to connect to broker\n")

    def on_disconnect(self, client, userdata, reason_code):
        self.connect_button.text = "Connect"
        self.connect_button.set_clicked_fn(self.run_program)

    def update_status(self, text: str = "", visible: bool = True, styles: object = error_styles):
        self.status_label.text = text
        self.status_label.visible = visible
        self.status_label.set_style(styles)

    def on_connect(self, client, userdata, flags, rc):
        self.update_status()
        if rc:
            error_mapping = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised",
            }
            self.update_status(error_mapping[rc])
            self.disconnect()
        self.connect_button.text = "Disconnect"
        self.connect_button.set_clicked_fn(self.disconnect)
        for topic, _, _ in self.get_topics_details():
            try:
                self.client.subscribe(topic)
            except ValueError as e:
                self.update_status(f"Invalid topic: {topic}")
                self.disconnect()
        self.update_status("Connected", styles=info_styles)

    def decode(self, message: str, type: Type):
        result = None
        match type:
            case Type.INT:
                result = int(message)
            case Type.FLOAT:
                result = float(message)
            case Type.STRING:
                result = message
            case Type.BOOL:
                result = bool(message)
            case Type.ARRAY_INT:
                result = list(map(int, list(json.loads(message))))
            case Type.ARRAY_FLOAT:
                result = list(map(float, list(json.loads(message))))
            case Type.ARRAY_STRING:
                result = list(map(str, list(json.loads(message))))
            case Type.ARRAY_BOOL:
                result = list(map(bool, list(json.loads(message))))
        return result

    def on_message(self, client, userdata, msg):
        self.update_status()
        for value in self.get_topics_details():
            if value[0] != msg.topic: 
                continue
            _, event, type = value
            message_str = msg.payload.decode("utf-8")
            try:
                message = self.decode(message_str, type)
                event_type = carb.events.type_from_string(event)
                bus.push(event_type, payload={"msg": message})
                self.update_status("Sent data on bus", styles=info_styles)
            except ValueError as e:
                self.update_status(f"Failed to convert input {message_str} to type {type.value}")
            except Exception as e:
                self.update_status(f"Failed to send data on bus: {e}")
                