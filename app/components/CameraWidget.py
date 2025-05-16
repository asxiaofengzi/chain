from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QMutex
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
import cv2
import numpy as np

class CameraWidget(QWidget):
    def __init__(self, camera_id=0, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.capture = None
        self.frame = None
        self.mutex = QMutex()
        self.paused = False
        self.title = f"摄像头 {camera_id + 1}"
        
        # 设置标签用于显示视频
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)  # 减少边距
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.camera_label)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D30;
                border-radius: 6px;
            }
            QLabel {
                border: 1px solid #3E3E42;
                border-radius: 4px;
                background-color: #252525;
                color: white;
            }
        """)
    
    def start(self):
        """启动摄像头"""
        try:
            self.capture = cv2.VideoCapture(self.camera_id)
            if not self.capture.isOpened():
                print(f"无法打开摄像头 {self.camera_id}")
                return False
            self.paused = False
            return True
        except Exception as e:
            print(f"启动摄像头时出错: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
    
    def pause(self):
        """暂停摄像头"""
        self.paused = True
    
    def resume(self):
        """恢复摄像头"""
        self.paused = False
    
    def get_frame(self):
        """获取当前帧"""
        if self.capture is None or self.paused:
            return self.frame
        
        ret, frame = self.capture.read()
        if ret:
            self.mutex.lock()
            self.frame = frame
            self.mutex.unlock()
            return frame
        return None
    
    def update_image(self, frame):
        """更新显示的图像"""
        if frame is None:
            return
        
        # 将OpenCV的BGR图像转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 获取图像尺寸
        height, width, channels = rgb_frame.shape
        
        # 创建QImage
        bytesPerLine = channels * width
        image = QImage(rgb_frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        
        # 根据窗口大小缩放图像
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(self.camera_label.width(), self.camera_label.height(),
                              Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 在图像上添加标题
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明背景
        painter.fillRect(0, 0, pixmap.width(), 30, QColor(0, 0, 0, 150))
        
        # 设置字体
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        
        # 绘制文本
        painter.setPen(Qt.white)
        painter.drawText(10, 20, self.title)
        
        painter.end()
        
        # 设置图像
        self.camera_label.setPixmap(pixmap)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放图像"""
        super().resizeEvent(event)
        if self.frame is not None:
            self.update_image(self.frame) 