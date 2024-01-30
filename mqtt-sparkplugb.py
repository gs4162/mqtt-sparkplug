#!/usr/bin/env python3
import ssl
import paho.mqtt.client as mqtt
import sparkplug_b_pb2  # Import the generated protobuf classes
import os
from pymongo import MongoClient
from google.protobuf.json_format import MessageToJson
import json

# MQTT Broker details
broker_address = os.getenv('MQTT_BROKER_ADDRESS', 'default_broker_address')
port = int(os.getenv('MQTT_PORT', 1883))

# MongoDB connection details
mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'root')
mongo_password = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'example')
mongo_host = "mongo-db"  # Use the Docker Compose service name for MongoDB
mongo_port = "27017"
mongo_db = "mqtt_data"
mongo_collection = "structured_messages"
mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"

# Connect to MongoDB
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db]
collection = db[mongo_collection]

# Directory containing certificates and keys
certs_dir = "./certs"

def find_cert_file(extension):
    for file in os.listdir(certs_dir):
        if file.endswith(extension):
            return os.path.join(certs_dir, file)
    return None

cert_path = find_cert_file('.crt')
key_path = find_cert_file('.key')
ca_path = find_cert_file('.pem')

if not all([cert_path, key_path, ca_path]):
    raise FileNotFoundError("Could not find all required certificate and key files.")

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")

def parse_payload_to_json(payload):
    # Convert protobuf message to JSON string and then to a dict
    json_str = MessageToJson(payload)
    return json.loads(json_str)

def on_message(client, userdata, msg):
    try:
        payload = sparkplug_b_pb2.Payload()
        payload.ParseFromString(msg.payload)
        payload_dict = parse_payload_to_json(payload)
        
        # Transform and extract relevant data
        message_document = {
            "topic": msg.topic,
            "timestamp": payload_dict.get("timestamp"),
            "metrics": payload_dict.get("metrics", []),
            "seq": payload_dict.get("seq")
        }
        
        # Insert transformed data into MongoDB
        collection.insert_one(message_document)
    except Exception as e:
        print(f"Failed to decode and store message: {e}")

client = mqtt.Client()
client.tls_set(ca_certs=ca_path, certfile=cert_path, keyfile=key_path, tls_version=ssl.PROTOCOL_TLSv1_2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address, port, 60)
client.loop_forever()
