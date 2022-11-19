from poooli import Poooli
import bluetooth
import os
import pymongo
import time
from dotenv import load_dotenv

load_dotenv()

socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

pli = Poooli(socket)
pli.connect(os.getenv("POOOLI_MAC"), channel=1)

client = pymongo.MongoClient(f"mongodb+srv://root:{os.getenv('POOOLI_DB_PASSWORD')}@cece.ldq20.mongodb.net/?retryWrites=true&w=majority")
db = client.cece
messages = db.messages

name = os.getenv("POOOLI_NAME")

while True:
    message = messages.find_one({"printed": False, "for": name})
    if message is not None:
        print("Printing message...")
        pli.send_image_bytes(message["image"])
    time.sleep(1)