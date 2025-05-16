import cv2
import numpy as np
from ultralytics import YOLO
import torch

class YoloDetector:
    def __init__(self, model_path=None, conf_threshold=0.25):
        """
        初始化YOLOv8检测器
        
        参数:
            model_path: YOLO模型路径，如果为None则加载预训练模型
            conf_threshold: 置信度阈值
        """
        self.conf_threshold = conf_threshold
        
        # 加载模型
        if model_path:
            self.model = YOLO(model_path)
        else:
            # 使用预训练模型yolov8n.pt
            self.model = YOLO("yolov8n.pt")
            
        # 存储最近的检测结果
        self.last_results = None
        
        # 确保使用GPU
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
    
    def detect(self, frame):
        """
        在图像上进行目标检测
        
        参数:
            frame: 输入图像
            
        返回:
            检测结果
        """
        # 使用YOLO进行检测
        results = self.model(frame, conf=self.conf_threshold, device=self.device)
        self.last_results = results[0]  # 获取第一个结果
        return self.last_results
    
    def draw_detections(self, frame):
        """
        在图像上绘制检测结果
        
        参数:
            frame: 输入图像
            
        返回:
            标记了检测结果的图像
        """
        if self.last_results is None:
            return frame
        
        # 创建图像副本
        annotated_frame = frame.copy()
        
        # 获取检测框、类别和置信度
        boxes = self.last_results.boxes.xyxy.cpu().numpy()
        classes = self.last_results.boxes.cls.cpu().numpy()
        confidences = self.last_results.boxes.conf.cpu().numpy()
        
        # 绘制每个检测框
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            cls_id = int(classes[i])
            conf = confidences[i]
            
            # 获取类别名称
            class_name = self.last_results.names[cls_id]
            
            # 绘制边界框
            color = (0, 255, 0)  # 绿色边框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制类别和置信度
            label = f"{class_name}: {conf:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated_frame
    
    def get_last_results(self):
        """
        获取最近的检测结果
        
        返回:
            最近的检测结果
        """
        return self.last_results 