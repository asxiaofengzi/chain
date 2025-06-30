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
        self.camera_defect_status = [False, False, False, False]  # 记录每个摄像头的缺陷检测状态
        self.defect_cameras = []  # 记录所有检测到缺陷的摄像头列表
        self.defect_details = {}  # 记录每个摄像头的详细缺陷信息
        self.video_mode = False  # 标记是否为视频演示模式
        
        # 缺陷类型中文映射
        self.defect_type_mapping = {
            'damage': '损坏',
            'misplace': '错位',
            'rough': '粗糙',
            'discard': '丢弃',
            'lowandhigh': '高低不平',
            'asymmetric': '不对称',
            'scratch': '划痕'
        }
        
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
                padding: 10px 20px;
                font-weight: bold;
                font-size: 16px;
                min-width: 120px;
                height: 42px;
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
        self.select_video_btn = QPushButton("选择视频")  # 新增选择视频按钮
        self.select_video_btn.setHidden(True)
        
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
        control_layout.addWidget(self.select_video_btn)  # 添加选择视频按钮
        
        # 添加弹性空间
        control_layout.addStretch(1)
        
        # 连接按钮信号到槽函数
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.mark_btn.clicked.connect(self.mark_defect)
        self.save_btn.clicked.connect(self.save_image)
        self.continue_btn.clicked.connect(self.continue_detection)  # 连接继续检测按钮信号
        self.select_video_btn.clicked.connect(self.select_video)  # 连接选择视频按钮信号
        
        # 添加标题标签
        title_label = QLabel("铁链缺陷检测系统")
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 添加布局到主布局
        main_layout.addWidget(title_label)
        main_layout.addLayout(camera_grid, 5)  # 视频流占据5/6的空间
        main_layout.addLayout(control_layout, 1)  # 控制按钮占据1/6的空间
    
    def start_detection(self):
        # 关闭视频模式
        self.video_mode = False
        
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
        self.select_video_btn.setEnabled(True)  # 启用选择视频按钮
        
        # 开始检测
        self.running = True
        self.defect_detected = False
        self.defect_camera_id = -1  # 重置检测到缺陷的摄像头ID
        self.camera_defect_status = [False, False, False, False]  # 重置每个摄像头的缺陷状态
        self.defect_cameras = []  # 重置缺陷摄像头列表
        self.defect_details = {}  # 重置缺陷详细信息
        self.timer.start(30)  # 约33FPS
    
    def stop_detection(self):
        # 停止检测
        self.running = False
        self.timer.stop()
        
        # 停止所有摄像头
        for camera in self.cameras:
            camera.stop()
        
        # 重置视频模式
        self.video_mode = False
        
        # 改变按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)  # 禁用继续检测按钮
        self.select_video_btn.setEnabled(True)  # 启用选择视频按钮
    
    def update_frames(self):
        if not self.running:
            return
        
        # 在每次更新开始时，清空当前轮次的缺陷检测信息
        current_defect_cameras = []
        current_defect_details = {}
        any_defect_detected = False
        
        # 获取每个摄像头的当前帧
        for i, camera in enumerate(self.cameras):
            # 在视频模式下，只处理第一个摄像头
            if self.video_mode and i > 0:
                continue
                
            frame = camera.get_frame()
            if frame is not None:
                self.current_frames[i] = frame.copy()
                
                # 进行检测（在实时模式下，总是进行检测以支持多摄像头）
                if not self.defect_detected or self.video_mode:
                    results = self.detector.detect(frame)
                    
                    if len(results.boxes) > 0:  # 检测到缺陷
                        # 在视频模式下，绘制检测结果但不暂停
                        if self.video_mode:
                            # 获取缺陷信息并输出到控制台
                            defect_info = self.get_defect_info(results)
                            print(f"视频模式 - 摄像头{i+1}检测到缺陷: {defect_info}")
                            
                            # 直接在视频帧上绘制检测结果
                            marked_frame = self.detector.draw_detections(frame)
                            camera.update_image(marked_frame)
                            continue
                        
                        # 实时检测模式：收集所有检测到缺陷的摄像头信息
                        any_defect_detected = True
                        current_defect_cameras.append(i)
                        current_defect_details[i] = self.get_defect_info(results)
                
                # 在没有检测到缺陷或视频模式下，正常更新图像
                if not self.defect_detected or self.video_mode:
                    camera.update_image(frame)
        
        # 如果检测到缺陷且不在视频模式下，处理检测结果
        if any_defect_detected and not self.video_mode and not self.defect_detected:
            self.defect_detected = True
            self.defect_cameras = current_defect_cameras
            self.defect_details = current_defect_details
            self.defect_camera_id = current_defect_cameras[0]  # 保持兼容性，使用第一个
            
            # 暂停所有摄像头
            for j in range(4):
                self.cameras[j].pause()
            
            # 发送低电平信号
            send_low_signal()
            
            # 改变按钮状态
            self.mark_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.continue_btn.setEnabled(True)
            
            # 生成多摄像头缺陷信息
            defect_summary = self.generate_multi_camera_defect_info()
            QMessageBox.information(self, "检测结果", defect_summary)
    
    def generate_multi_camera_defect_info(self):
        """
        生成多摄像头缺陷检测的汇总信息
        
        返回:
            包含所有检测到缺陷的摄像头信息的字符串
        """
        if not self.defect_cameras:
            return "未检测到缺陷"
        
        camera_count = len(self.defect_cameras)
        
        if camera_count == 1:
            # 单个摄像头检测到缺陷
            camera_id = self.defect_cameras[0]
            return f"摄像头 {camera_id + 1} 检测到缺陷!\n\n{self.defect_details[camera_id]}"
        else:
            # 多个摄像头检测到缺陷
            summary = f"⚠️ 同时有 {camera_count} 个摄像头检测到缺陷!\n\n"
            
            for i, camera_id in enumerate(self.defect_cameras):
                summary += f"📹 摄像头 {camera_id + 1}:\n"
                # 移除"检测到的缺陷类型:"前缀，直接显示缺陷信息
                defect_info = self.defect_details[camera_id]
                clean_info = defect_info.replace("检测到的缺陷类型:\n", "")
                summary += clean_info
                
                if i < camera_count - 1:  # 不是最后一个摄像头
                    summary += "\n" + "-" * 30 + "\n"
            
            return summary

    def get_defect_info(self, results):
        """
        解析检测结果，返回中文缺陷信息
        
        参数:
            results: YOLO检测结果
            
        返回:
            包含缺陷类型和置信度的中文描述字符串
        """
        defect_info = "检测到的缺陷类型:\n"
        
        # 获取检测框、类别和置信度
        classes = results.boxes.cls.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        
        # 统计每种缺陷类型
        defect_counts = {}
        for i, cls_id in enumerate(classes):
            cls_id = int(cls_id)
            conf = confidences[i]
            
            # 获取类别名称
            class_name = results.names[cls_id]
            
            # 转换为中文名称
            chinese_name = self.defect_type_mapping.get(class_name, class_name)
            
            # 统计缺陷数量和最高置信度
            if chinese_name not in defect_counts:
                defect_counts[chinese_name] = {'count': 0, 'max_conf': 0}
            
            defect_counts[chinese_name]['count'] += 1
            defect_counts[chinese_name]['max_conf'] = max(defect_counts[chinese_name]['max_conf'], conf)
        
        # 生成缺陷信息字符串
        for defect_name, info in defect_counts.items():
            count = info['count']
            max_conf = info['max_conf']
            defect_info += f"• {defect_name}: {count}处 (置信度: {max_conf:.2f})\n"
        
        return defect_info.rstrip()  # 移除最后的换行符

    def mark_defect(self):
        # 标记当前帧上的缺陷
        if self.defect_detected or self.video_mode:
            for i, frame in enumerate(self.current_frames):
                if frame is not None:
                    # 在视频模式下，只处理第一个摄像头
                    if self.video_mode and i > 0:
                        continue
                    
                    # 在实时检测模式下，只对检测到缺陷的摄像头或活跃的摄像头进行标注
                    if not self.video_mode:
                        # 检查摄像头是否正在运行
                        camera = self.cameras[i]
                        if camera.capture is None:
                            continue  # 跳过未启动的摄像头
                    
                    # 对当前帧重新进行检测以获取准确的检测结果
                    results = self.detector.detect(frame)
                    if len(results.boxes) > 0:
                        # 只有检测到缺陷的摄像头才显示标注
                        marked_frame = self.detector.draw_detections(frame)
                        self.cameras[i].update_image(marked_frame)
                    else:
                        # 没有检测到缺陷的摄像头显示原始图像
                        self.cameras[i].update_image(frame)
    
    def save_image(self):
        # 保存当前帧
        if self.video_mode:
            # 视频模式：保存第一个摄像头
            self._save_single_camera_image(0, "video")
        elif self.defect_detected and self.defect_cameras:
            # 实时检测模式：保存所有检测到缺陷的摄像头
            saved_cameras = []
            for camera_id in self.defect_cameras:
                if self._save_single_camera_image(camera_id, f"camera_{camera_id+1}"):
                    saved_cameras.append(camera_id + 1)
            
            if saved_cameras:
                today = datetime.datetime.now().strftime("%Y%m%d")
                save_dir = os.path.join("defects", today)
                camera_list = "、".join([f"摄像头{cam}" for cam in saved_cameras])
                QMessageBox.information(self, "保存成功", f"已保存 {camera_list} 的缺陷图像到 {save_dir}")
        else:
            QMessageBox.warning(self, "保存失败", "没有检测到缺陷，无法保存图像")
    
    def _save_single_camera_image(self, camera_id, prefix):
        """
        保存单个摄像头的图像
        
        参数:
            camera_id: 摄像头ID
            prefix: 文件名前缀
            
        返回:
            bool: 是否保存成功
        """
        # 创建保存目录
        today = datetime.datetime.now().strftime("%Y%m%d")
        save_dir = os.path.join("defects", today)
        os.makedirs(save_dir, exist_ok=True)
        
        # 获取摄像头的当前帧
        frame = self.current_frames[camera_id]
        if frame is not None:
            # 重新检测该帧以获取准确的检测结果
            results = self.detector.detect(frame)
            if len(results.boxes) > 0 or self.video_mode:
                # 获取标记后的帧
                marked_frame = self.detector.draw_detections(frame)
                
                # 使用时间作为文件名，避免覆盖
                time_str = datetime.datetime.now().strftime("%H%M%S")
                save_path = os.path.join(save_dir, f"{prefix}_{time_str}.jpg")
                
                cv2.imwrite(save_path, marked_frame)
                
                if self.video_mode:
                    QMessageBox.information(self, "保存成功", f"已保存视频帧缺陷图像到 {save_dir}")
                
                return True
        
        return False
    
    def continue_detection(self):
        """继续检测，清除当前检测结果并重新开始检测"""
        print("继续检测按钮被点击")
        
        if not self.running:
            print("检测未在运行状态，无法继续")
            return
            
        # 重置检测状态
        self.defect_detected = False
        self.camera_defect_status = [False, False, False, False]  # 重置每个摄像头的缺陷状态
        self.defect_cameras = []  # 重置缺陷摄像头列表
        self.defect_details = {}  # 重置缺陷详细信息
        
        # 如果在视频模式下，不需要恢复摄像头（因为视频模式下没有暂停）
        if not self.video_mode:
            # 恢复所有摄像头
            for camera in self.cameras:
                camera.resume()
        
        # 更新按钮状态
        self.mark_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        self.select_video_btn.setEnabled(True)  # 启用选择视频按钮
        
        # 重新开始检测
        self.timer.start(30)
    
    def select_video(self):
        """选择视频文件进行演示检测"""
        # 停止当前正在进行的检测
        if self.running:
            self.stop_detection()
        
        # 打开文件选择对话框
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*)", options=options
        )
        
        if not file_path:
            return  # 用户取消了选择
            
        # 设置视频模式标志
        self.video_mode = True
        
        # 为第一个摄像头窗口加载视频文件
        if self.cameras[0].set_video_file(file_path):
            # 改变按钮状态
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.mark_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.continue_btn.setEnabled(False)
            self.select_video_btn.setEnabled(False)
            
            # 开始检测
            self.running = True
            self.defect_detected = False
            self.timer.start(30)  # 约33FPS
            
            QMessageBox.information(self, "视频模式", "已进入视频演示模式，检测到缺陷时不会停止视频播放。")
        else:
            self.video_mode = False
            QMessageBox.critical(self, "错误", "无法打开视频文件，请确认文件格式正确。")
    
    def closeEvent(self, event):
        # 程序关闭时停止所有摄像头
        self.stop_detection()
        event.accept()
