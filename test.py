import cv2


def main():
    # 初始化摄像头（0表示默认摄像头，其他数字可切换外接摄像头）
    cap = cv2.VideoCapture(1)

    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("错误：无法打开摄像头")
        return

    # 可选：设置摄像头分辨率（例如1280x720）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)

    print("摄像头已启动，按 'q' 键退出...")

    try:
        while True:
            # 逐帧捕获
            ret, frame = cap.read()

            # 如果帧读取失败
            if not ret:
                print("错误：无法接收帧（视频流结束？）")
                break

            # 显示帧（可在此处添加图像处理代码）
            cv2.imshow('实时摄像头', frame)

            # 按下 'q' 键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        print("摄像头已关闭")


if __name__ == "__main__":
    main()