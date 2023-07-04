import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new
import zlib
import requests
import torch



model = torch.hub.load('ultralytics/yolov5', 'custom', path='best2.pt') # carica il modello personalizzato con i pesi addestrati

# Imposta il modello in modalità valutazione
model.eval()

# URL del server web
url = 'http://192.168.153.59:5000/api/stampa'

params_STOP = {
    'nome': 'pedone',
}

params_GO = {
    'nome': 'go',
}

# Crea un'istanza di Model con l'architettura predefinita "yolov5s"

HOST=''
PORT=8485

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()

data = b""
payload_size = struct.calcsize(">L")
#print("payload_size: {}".format(payload_size))
while True:
    while len(data) < payload_size:
        #print("Recv: {}".format(len(data)))
        data += conn.recv(4096)

   # print("Done Recv: {}".format(len(data)))
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    #print("msg_size: {}".format(msg_size))
    while len(data) < msg_size:
        data += conn.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    #cv2.imshow('ImageWindow',frame)
    #height, width, channels = frame.shape
    #print("Altezza:", height)
    #print("Larghezza:", width)
    new_width = 352
    new_height = 352

    frame = cv2.resize(frame, (new_width, new_height))
    print(frame.shape)
    results = model(frame)
    #print(results.xyxy[0])
    list = []
    for result in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = result
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f'{model.names[int(cls)]} {conf:.2f}', (int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        list.append(model.names[int(cls)])
    cv2.imshow('Object Detection',frame)
    #print(list)
    
    #if "pedone" in list:
        # Invio della richiesta GET
        #print("pedone")
        #response = requests.get(url, params=params_STOP)
   # else:
      #  None
        #print("nessun pedone")
        # Invio della richiesta GET
        #response = requests.get(url, params=params_GO)
        
    cv2.waitKey(1)