import cv2
import numpy as np
import time

def test_camera(camera_id=4, duration=30):
    """
    测试指定ID的摄像头
    
    参数:
        camera_id: 摄像头ID，默认为4
        duration: 测试持续时间（秒），默认30秒
    """
    print(f"正在尝试打开摄像头 ID: {camera_id}")
    
    # 尝试打开摄像头
    cap = cv2.VideoCapture(camera_id)
    
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print(f"错误: 无法打开摄像头 ID: {camera_id}")
        return False
    
    print(f"成功打开摄像头 ID: {camera_id}")
    print(f"摄像头信息:")
    print(f"- 宽度: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}")
    print(f"- 高度: {int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"- FPS: {cap.get(cv2.CAP_PROP_FPS)}")
    
    # 创建窗口
    window_name = f"摄像头测试 (ID: {camera_id})"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # 帧计数和起始时间
    frame_count = 0
    start_time = time.time()
    fps_update_time = start_time
    fps = 0
    
    print(f"开始测试，将持续 {duration} 秒...")
    print("按 'q' 键退出，按 's' 键保存当前帧")
    
    try:
        while True:
            # 读取一帧
            ret, frame = cap.read()
            
            # 检查是否成功读取
            if not ret:
                print("警告: 无法读取帧")
                break
            
            # 计算FPS
            frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # 每秒更新一次FPS显示
            if current_time - fps_update_time >= 1.0:
                fps = frame_count / (current_time - fps_update_time)
                frame_count = 0
                fps_update_time = current_time
            
            # 在图像上显示信息
            cv2.putText(frame, f"摄像头 ID: {camera_id}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"运行时间: {elapsed_time:.1f}秒", (10, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, "按 's' 保存图像, 按 'q' 退出", (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # 显示图像
            cv2.imshow(window_name, frame)
            
            # 检查是否到达持续时间
            if elapsed_time >= duration:
                print(f"测试完成，持续了 {elapsed_time:.2f} 秒")
                break
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("用户中断测试")
                break
            elif key == ord('s'):
                # 保存当前帧
                filename = f"camera_{camera_id}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"图像已保存为: {filename}")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    
    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        print("摄像头测试结束")
        
        return True

if __name__ == "__main__":
    # 测试指定的摄像头
    # test_camera(camera_id=4, duration=60)  # 测试60秒 
    for i in range(10):
        test_camera(camera_id=i, duration=60)  # 测试60秒 