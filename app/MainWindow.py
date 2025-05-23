from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGridLayout, QMessageBox, QFileDialog,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QFont
from .components.CameraWidget import CameraWidget
from .detector.YoloDetector import YoloDetector
from .utils.io_control import send_low_signal
import cv2
import os
import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("铁链缺陷检测系统")
        self.setMinimumSize(1200, 800)
          # 初始化组件
        self.cameras = []
        self.detector = YoloDetector(model_path="best.pt")
        self.running = False
        self.defect_detected = False
        self.defect_camera_id = -1  # 记录检测到缺陷的摄像头ID
        self.current_frames = [None, None, None, None]
        
        # 设置中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
                height: 36px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #707070;
            }
            QLabel {
                color: white;
            }
        """)
        
        # 创建布局
        self.setup_ui()
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        
    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # 摄像头网格布局 - 使用2x2网格
        camera_grid = QGridLayout()
        camera_grid.setSpacing(10)  # 设置摄像头之间的间距
        
        # 创建四个摄像头窗口
        for i in range(4):
            camera_widget = CameraWidget(camera_id=i)
            self.cameras.append(camera_widget)
            row, col = i // 2, i % 2
            camera_grid.addWidget(camera_widget, row, col)
        
        # 控制按钮布局
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)  # 按钮之间的间距
        
        # 创建控制按钮
        self.start_btn = QPushButton("开始检测")
        self.stop_btn = QPushButton("停止检测")
        self.mark_btn = QPushButton("标记缺陷")
        self.save_btn = QPushButton("保存图像")
        self.continue_btn = QPushButton("继续检测")  # 新增继续检测按钮
        
        # 设置按钮状态
        self.stop_btn.setEnabled(False)
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)  # 默认禁用继续检测按钮
        
        # 添加弹性空间，使按钮居中
        control_layout.addStretch(1)
        
        # 添加按钮到控制布局
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.mark_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.continue_btn)  # 将继续检测按钮添加到布局
        
        # 添加弹性空间
        control_layout.addStretch(1)
        
        # 连接按钮信号到槽函数
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.mark_btn.clicked.connect(self.mark_defect)
        self.save_btn.clicked.connect(self.save_image)
        self.continue_btn.clicked.connect(self.continue_detection)  # 连接继续检测按钮信号
        
        # 添加标题标签
        title_label = QLabel("铁链缺陷检测系统")
        title_font = QFont("Arial", 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 添加布局到主布局
        main_layout.addWidget(title_label)
        main_layout.addLayout(camera_grid, 5)  # 视频流占据5/6的空间
        main_layout.addLayout(control_layout, 1)  # 控制按钮占据1/6的空间
    
    def start_detection(self):
        # 启动所有摄像头
        for i, camera in enumerate(self.cameras):
            if not camera.start():
                QMessageBox.critical(self, "错误", f"无法启动摄像头 {i+1}，请检查连接")
                return
        
        # 改变按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)  # 禁用继续检测按钮
          # 开始检测
        self.running = True
        self.defect_detected = False
        self.defect_camera_id = -1  # 重置检测到缺陷的摄像头ID
        self.timer.start(30)  # 约33FPS
    
    def stop_detection(self):
        # 停止检测
        self.running = False
        self.timer.stop()
        
        # 停止所有摄像头
        for camera in self.cameras:
            camera.stop()
        
        # 改变按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)  # 禁用继续检测按钮
    
    def update_frames(self):
        if not self.running:
            return
        
        # 获取每个摄像头的当前帧
        for i, camera in enumerate(self.cameras):
            frame = camera.get_frame()
            if frame is not None:
                self.current_frames[i] = frame.copy()
                  # 进行检测
                if not self.defect_detected:
                    results = self.detector.detect(frame)
                    if len(results.boxes) > 0:  # 检测到缺陷
                        self.defect_detected = True
                        self.defect_camera_id = i  # 记录检测到缺陷的摄像头ID
                        for j in range(4):
                            self.cameras[j].pause()  # 暂停所有摄像头
                        
                        # 发送低电平信号
                        send_low_signal()
                        
                        # 改变按钮状态
                        self.mark_btn.setEnabled(True)
                        self.save_btn.setEnabled(True)
                        self.continue_btn.setEnabled(True)  # 启用继续检测按钮
                        
                        QMessageBox.information(self, "检测结果", f"摄像头 {i+1} 检测到缺陷!")
                
                # 用检测结果更新摄像头视图
                camera.update_image(frame)
    
    def mark_defect(self):
        # 标记当前帧上的缺陷
        if self.defect_detected:
            for i, frame in enumerate(self.current_frames):
                if frame is not None:                    # 获取标记后的帧
                    marked_frame = self.detector.draw_detections(frame)
                    self.cameras[i].update_image(marked_frame)
    
    def save_image(self):
        # 保存当前帧
        if self.defect_detected and self.defect_camera_id >= 0:
            # 创建保存目录 - 只使用年月日
            today = datetime.datetime.now().strftime("%Y%m%d")
            save_dir = os.path.join("defects", today)
            os.makedirs(save_dir, exist_ok=True)
            
            # 只保存检测到缺陷的摄像头图像
            frame = self.current_frames[self.defect_camera_id]
            if frame is not None:
                # 获取标记后的帧
                marked_frame = self.detector.draw_detections(frame)
                
                # 使用时间作为文件名，避免覆盖
                time_str = datetime.datetime.now().strftime("%H%M%S")
                save_path = os.path.join(save_dir, f"camera_{self.defect_camera_id+1}_{time_str}.jpg")
                
                cv2.imwrite(save_path, marked_frame)
                QMessageBox.information(self, "保存成功", f"已保存摄像头 {self.defect_camera_id+1} 的缺陷图像到 {save_dir}")
    
    def continue_detection(self):
        """继续检测，清除当前检测结果并重新开始检测"""
        print("继续检测按钮被点击")
        
        if not self.running:
            print("检测未在运行状态，无法继续")
            return
            
        # 重置检测状态
        self.defect_detected = False
        
        # 恢复所有摄像头
        for camera in self.cameras:
            camera.resume()
        
        # 更新按钮状态
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        
        # 重新开始检测
        self.timer.start(30)
    
    def closeEvent(self, event):
        # 程序关闭时停止所有摄像头
        self.stop_detection()
        event.accept()