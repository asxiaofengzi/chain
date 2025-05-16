import os
import cv2
import argparse
import time
from pathlib import Path
from ultralytics import YOLO
import numpy as np
import shutil

def process_images(input_dir, output_dir, model_path="best.pt", conf_threshold=0.25, save_annotated=True, save_crops=False):
    """
    使用YOLOv8模型处理指定文件夹中的所有图片
    
    参数:
        input_dir: 输入图片目录
        output_dir: 输出结果目录
        model_path: 模型路径
        conf_threshold: 置信度阈值
        save_annotated: 是否保存标注后的图片
        save_crops: 是否保存裁剪的缺陷区域
    """
    print(f"正在加载模型: {model_path}")
    model = YOLO(model_path)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果需要保存裁剪区域，创建裁剪目录
    crops_dir = os.path.join(output_dir, "crops")
    if save_crops:
        os.makedirs(crops_dir, exist_ok=True)
    
    # 获取所有图片文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(list(Path(input_dir).glob(f"*{ext}")))
        image_files.extend(list(Path(input_dir).glob(f"*{ext.upper()}")))
    
    if not image_files:
        print(f"在 {input_dir} 中未找到图片文件")
        return
    
    print(f"发现 {len(image_files)} 个图片文件")
    
    # 创建结果CSV文件
    csv_path = os.path.join(output_dir, "results.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("文件名,检测时间(ms),检测到的缺陷数,类别,置信度,坐标\n")
    
    # 处理每个图片
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        print(f"正在处理: {img_name}")
        
        # 读取图片
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"无法读取图片: {img_path}")
            continue
        
        # 记录检测时间
        start_time = time.time()
        
        # 使用模型检测
        results = model(img, conf=conf_threshold)[0]
        
        # 计算检测时间
        detection_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 获取检测结果
        boxes = results.boxes.xyxy.cpu().numpy() if len(results.boxes) > 0 else []
        classes = results.boxes.cls.cpu().numpy() if len(results.boxes) > 0 else []
        confidences = results.boxes.conf.cpu().numpy() if len(results.boxes) > 0 else []
        class_names = results.names
        
        # 保存结果到CSV
        with open(csv_path, 'a', encoding='utf-8') as f:
            if len(boxes) == 0:
                f.write(f"{img_name},{detection_time:.2f},0,无,0,无\n")
            else:
                for i, box in enumerate(boxes):
                    cls_id = int(classes[i])
                    conf = confidences[i]
                    cls_name = class_names[cls_id]
                    coords = ','.join([f"{coord:.2f}" for coord in box])
                    
                    # 如果是第一个检测框，写入文件名和检测时间
                    if i == 0:
                        f.write(f"{img_name},{detection_time:.2f},{len(boxes)},{cls_name},{conf:.4f},{coords}\n")
                    else:
                        f.write(f",,,{cls_name},{conf:.4f},{coords}\n")
        
        # 如果需要保存标注后的图片
        if save_annotated:
            # 使用模型的绘图功能
            annotated_img = results.plot()
            
            # 保存标注后的图片
            annotated_path = os.path.join(output_dir, f"annotated_{img_name}")
            cv2.imwrite(annotated_path, annotated_img)
        
        # 如果需要保存裁剪区域
        if save_crops and len(boxes) > 0:
            # 为每个图片创建子目录
            img_crops_dir = os.path.join(crops_dir, os.path.splitext(img_name)[0])
            os.makedirs(img_crops_dir, exist_ok=True)
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                cls_id = int(classes[i])
                conf = confidences[i]
                cls_name = class_names[cls_id]
                
                # 裁剪区域
                crop = img[y1:y2, x1:x2]
                
                # 保存裁剪区域
                crop_filename = f"{cls_name}_{conf:.2f}_{i}.jpg"
                crop_path = os.path.join(img_crops_dir, crop_filename)
                cv2.imwrite(crop_path, crop)
    
    print(f"处理完成！检测结果保存在: {output_dir}")
    print(f"结果摘要保存为: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用YOLOv8批量检测图片中的铁链缺陷")
    parser.add_argument("--input", "-i", type=str, default="D:\yolo\pic", help="输入图片目录")
    parser.add_argument("--output", "-o", type=str, default="results", help="输出结果目录")
    parser.add_argument("--model", "-m", type=str, default="best.pt", help="YOLOv8模型路径")
    parser.add_argument("--conf", "-c", type=float, default=0.1, help="置信度阈值")
    parser.add_argument("--no-save", action="store_false", dest="save_annotated", help="不保存标注后的图片")
    parser.add_argument("--crops", action="store_true", help="保存裁剪的缺陷区域")
    
    args = parser.parse_args()
    
    process_images(
        input_dir=args.input, 
        output_dir=args.output, 
        model_path=args.model,
        conf_threshold=args.conf,
        save_annotated=args.save_annotated,
        save_crops=args.crops
    ) 