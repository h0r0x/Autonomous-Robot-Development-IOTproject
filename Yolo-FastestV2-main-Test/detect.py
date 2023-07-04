import os
import cv2
import time
import argparse

import torch
import model.detector
import utils.utils

cap = cv2.VideoCapture(0)
    
# Imposta le dimensioni desiderate per il frame
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 128)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 128)

def capture_from_webcam():
    ret, frame = cap.read()
    return frame


start_time = time.time()
parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, default='', 
                    help='Specify training profile *.data')
parser.add_argument('--weights', type=str, default='', 
                    help='The path of the .pth model to be transformed')
parser.add_argument('--img', type=str, default='', 
                    help='The path of test image')

opt = parser.parse_args()
cfg = utils.utils.load_datafile(opt.data)
assert os.path.exists(opt.weights), "请指定正确的模型路径"
assert os.path.exists(opt.img), "请指定正确的测试图像路径"

#模型加载
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.detector.Detector(cfg["classes"], cfg["anchor_num"], True).to(device)
model.load_state_dict(torch.load(opt.weights, map_location=device))

#sets the module in eval node
model.eval()
end_time = time.time()

print("Tempo di caricamento del modello: {:.2f} secondi".format(end_time - start_time))

# Codice da misurare

while True:

    #pre-elaborazione dei dati
    start_time = time.time()
    ori_img = capture_from_webcam()
    res_img = cv2.resize(ori_img, (cfg["width"], cfg["height"]), interpolation = cv2.INTER_LINEAR) 
    img = res_img.reshape(1, cfg["height"], cfg["width"], 3)
    img = torch.from_numpy(img.transpose(0,3, 1, 2))
    img = img.to(device).float() / 255.0
    end_time = time.time()
    
    print("Tempo per cattura immagine: {:.2f} secondi".format(end_time - start_time))
    
    start_time = time.time()
    preds = model(img)
    end_time = time.time()
    
    print("Tempo di valutazione: {:.2f} secondi".format(end_time - start_time))

    #post-elaborazione
    output = utils.utils.handel_preds(preds, cfg, device)
    output_boxes = utils.utils.non_max_suppression(output, conf_thres = 0.3, iou_thres = 0.4)

    #caricare i nomi delle etichette
    LABEL_NAMES = []
    with open(cfg["names"], 'r') as f:
        for line in f.readlines():
            LABEL_NAMES.append(line.strip())

    h, w, _ = ori_img.shape
    scale_h, scale_w = h / cfg["height"], w / cfg["width"]

    #disegna il bounding box di previsione
    for box in output_boxes[0]:
        box = box.tolist()
        
        obj_score = box[4]
        category = LABEL_NAMES[int(box[5])]
        if category == "person":
            print("Classe: {}, score: {:.2f}".format(category, obj_score))
            x1, y1 = int(box[0] * scale_w), int(box[1] * scale_h)
            x2, y2 = int(box[2] * scale_w), int(box[3] * scale_h)

            cv2.rectangle(ori_img, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(ori_img, '%.2f' % obj_score, (x1, y1 - 5), 0, 0.7, (0, 255, 0), 2)	
            cv2.putText(ori_img, category, (x1, y1 - 25), 0, 0.7, (0, 255, 0), 2)

    cv2.imshow("frame", ori_img)
        
    # Attendere 1 millisecondo per l'input dell'utente
    key = cv2.waitKey(1)
    
    # Controlla se il tasto "q" è stato premuto
    if key == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()