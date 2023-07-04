import torch
import cv2

# Crea un'istanza di Model con l'architettura predefinita "yolov5s"
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best2.pt') # carica il modello personalizzato con i pesi addestrati

# Carica i pesi del modello dal file "best.pt"
#model.load_state_dict(torch.load("best.pt", map_location=torch.device('cpu'))['model'].float().state_dict())

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)

while True:
    # Acquisisci il frame dalla webcam
    ret, frame = cap.read()
    
    results = model(frame)
    
    for result in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = result
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f'{model.names[int(cls)]} {conf:.2f}', (int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('Object Detection',frame)
    
    #if len(results.xyxy[0]) > 0:
    #    for result in results.xyxy[0]:
    #        x1, y1, x2, y2, conf, cls = result
    #        print(f'{model.names[int(cls)]} {conf:.2f}')
    #else:
    #    print("none")
    
    
    
    # Attendi il tasto 'q' per uscire dal loop
    if cv2.waitKey(1) == ord('q'):
        break

# Rilascia la webcam e chiudi la finestra dell'object detection
cap.release()
cv2.destroyAllWindows()
