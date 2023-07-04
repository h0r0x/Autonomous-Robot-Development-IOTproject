import argparse
import cv2
import torch
import time
import os
import utils.utils
import model.detector

if __name__ == '__main__':
    # Specifica il file di configurazione per l'addestramento
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='', 
                        help='Specificare il file di configurazione per l\'addestramento *.data')
    parser.add_argument('--weights', type=str, default='', 
                        help='Il percorso del modello .pth da caricare')
    opt = parser.parse_args()
    
    cfg = utils.utils.load_datafile(opt.data)
    assert os.path.exists(opt.weights), "Si prega di specificare un percorso valido per il modello"
    
    # Carica il modello
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.detector.Detector(cfg["classes"], cfg["anchor_num"], True).to(device)
    model.load_state_dict(torch.load(opt.weights, map_location=device))
    
    # Imposta il modello in modalità valutazione (evaluation)
    model.eval()
    
    # Carica i nomi delle classi
    LABEL_NAMES = []
    with open(cfg["names"], 'r') as f:
        for line in f.readlines():
            LABEL_NAMES.append(line.strip())
    
    # Cattura i frame dalla webcam
    video_capture = cv2.VideoCapture(0)  # 0 indica la webcam predefinita
    while True:
        ret, frame = video_capture.read()
        
        # Preprocessa l'immagine
        res_img = cv2.resize(frame, (cfg["width"], cfg["height"]), interpolation=cv2.INTER_LINEAR) 
        img = res_img.reshape(1, cfg["height"], cfg["width"], 3)
        img = torch.from_numpy(img.transpose(0, 3, 1, 2))
        img = img.to(device).float() / 255.0
        
        # Esegui l'inferenza del modello
        start = time.perf_counter()
        preds = model(img)
        end = time.perf_counter()
        inference_time = (end - start) * 1000.0
        print("Tempo di inferenza: %.2f ms" % inference_time)
        
        # Elabora le previsioni
        output = utils.utils.handel_preds(preds, cfg, device)
        output_boxes = utils.utils.non_max_suppression(output, conf_thres=0.3, iou_thres=0.4)
        
        h, w, _ = frame.shape
        scale_h, scale_w = h / cfg["height"], w / cfg["width"]
        
        # Disegna i bounding box sul frame
        for box in output_boxes[0]:
            box = box.tolist()
            
            obj_score = box[4]
            category = LABEL_NAMES[int(box[5])]
            
            x1, y1 = int(box[0] * scale_w), int(box[1] * scale_h)
            x2, y2 = int(box[2] * scale_w), int(box[3] * scale_h)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(frame, '%.2f' % obj_score, (x1, y1 - 5), 0, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, category, (x1, y1 - 25), 0, 0.7, (0, 255, 0), 2)
        
        # Mostra il frame elaborato
        cv2.imshow('Webcam', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Rilascia la cattura video e chiudi le finestre
    video_capture.release()
    cv2.destroyAllWindows()
