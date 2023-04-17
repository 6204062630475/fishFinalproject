import cv2
import torch
import numpy as np        
        
model = torch.hub.load('ultralytics/yolov5', 'custom',path='fishtrainIV0.89.pt',force_reload=True)
area=[(80,15),(80,458),(600,458),(600,15)]
class VideoCamera(object):
    def __init__(self):

        self.video = cv2.VideoCapture(0)    

    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        if not success:
            assert not isinstance(image,type(None)), 'frame not found'
        results=model(image)
        # a=np.squeeze(results.render());;;
        list=[]
        for index, row in results.pandas().xyxy[0].iterrows():
            x1 = int(row['xmin'])
            y1 = int(row['ymin'])
            x2 = int(row['xmax'])
            y2 = int(row['ymax'])
            d=(row['name'])
            cx=int(x1+x2)//2
            cy=int(y1+y2)//2
            if 'fish' in d:
                results=cv2.pointPolygonTest(np.array(area,np.int32),((cx,cy)),False)
                if results >= 0:
                    # print(d)                
                    cv2.rectangle(image,(x1,y1),(x2,y2),(0,0,255),3)
                    cv2.putText(image,str(d),(x1,y1),cv2.FONT_HERSHEY_PLAIN,2,(255,0,0),2)
                    list.append([cx])
        cv2.polylines(image,[np.array(area,np.int32)],True,(0,255,0),2)
        a=(len(list))
        #print(a)
        cv2.putText(image,str(a),(15,30),cv2.FONT_HERSHEY_PLAIN,2,(0,0,255),2)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes(),a