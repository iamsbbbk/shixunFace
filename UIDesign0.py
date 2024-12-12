# -*- coding: utf-8 -*-


import sys
import os
import cv2
import numpy as np
import face_recognition
import pymysql
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QLabel, QVBoxLayout,
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QMainWindow, QApplication
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from FaceTool import FaceTools
from FaceSQL import FaceSQL

# 定义主窗口类MyWindow，继承自QMainWindow，用于构建人脸识别系统的图形界面及相关功能实现
class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()

        # 设置窗口标题为"人脸识别系统"
        self.setWindowTitle("人脸识别系统")
        # 设置窗口初始大小为宽900像素，高600像素
        self.resize(900, 600)

        # 初始化数据库操作类FaceSQL的实例，用于与数据库进行交互（如插入、查询数据等操作）
        self.facesql = FaceSQL()
        # 初始化人脸工具类FaceTools的实例，用于处理人脸数据（如编码转换、添加人脸数据等操作），并传入facesql实例以关联数据库操作
        self.facetools = FaceTools(self.facesql)

        # 创建主窗口的中心部件，后续的各种布局和控件都将添加到这个部件上
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 创建一个水平布局作为主布局，用于放置摄像头显示区域和右侧控制区布局
        main_layout = QHBoxLayout(main_widget)
        # 设置布局的外边距，上下左右均为20像素，使布局内的控件与窗口边缘有一定间隔
        main_layout.setContentsMargins(20, 20, 20, 20)
        # 设置布局内控件之间的间距为20像素
        main_layout.setSpacing(20)

        # 左侧摄像头显示区域相关设置
        self.cameraLabel = QLabel()
        # 设置摄像头显示区域的固定大小为宽640像素，高480像素
        self.cameraLabel.setFixedSize(640, 480)
        # 设置样式表，给显示区域添加1像素灰色实线边框，并设置背景颜色为黑色
        self.cameraLabel.setStyleSheet("border: 1px solid #ccc; background-color: #000;")
        # 设置图像自适应标签大小，使得摄像头捕获的图像能自动缩放填充显示区域
        self.cameraLabel.setScaledContents(True)
        # 将摄像头显示标签添加到主布局中
        main_layout.addWidget(self.cameraLabel)

        # 右侧控制区布局相关设置
        right_layout = QVBoxLayout()
        # 设置右侧布局内控件之间的间距为30像素
        right_layout.setSpacing(30)
        # 将右侧布局添加到主布局中，这样主布局就包含了左侧摄像头显示区和右侧控制区两部分
        main_layout.addLayout(right_layout)

        # 表单布局：用于学号(id)和姓名(name)输入框的布局设置
        form_layout = QFormLayout()
        # 设置表单布局内控件之间的间距为20像素
        form_layout.setSpacing(20)
        self.lineEdit_id = QLineEdit()
        self.lineEdit_name = QLineEdit()

        # 美化学号输入框的样式，设置边框、边框圆角、内边距以及字体大小等样式属性，并且当输入框获得焦点时改变边框颜色
        self.lineEdit_id.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        # 美化姓名输入框的样式，与学号输入框类似
        self.lineEdit_name.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)

        # 将"输入学号:"标签和学号输入框添加到表单布局中作为一行
        form_layout.addRow("输入学号:", self.lineEdit_id)
        # 将"输入姓名:"标签和姓名输入框添加到表单布局中作为另一行
        form_layout.addRow("输入姓名:", self.lineEdit_name)

        # 使用水平布局和弹性空间，使表单布局在水平方向上居中显示
        form_container = QHBoxLayout()
        form_container.addStretch()
        form_container.addLayout(form_layout)
        form_container.addStretch()
        right_layout.addLayout(form_container)

        # 按钮区域相关设置
        self.pushButton_submit = QPushButton("提交")
        self.pushButton_recognize = QPushButton("识别")
        self.pushButton_open_cam = QPushButton("开启摄像头")
        self.pushButton_close_cam = QPushButton("关闭摄像头")
        self.pushButton_exit = QPushButton("退出")

        btn_layout = QHBoxLayout()
        # 设置按钮布局内按钮之间的间距为15像素
        btn_layout.setSpacing(15)
        btn_layout.addWidget(self.pushButton_submit)
        btn_layout.addWidget(self.pushButton_recognize)
        btn_layout.addWidget(self.pushButton_open_cam)
        btn_layout.addWidget(self.pushButton_close_cam)
        btn_layout.addWidget(self.pushButton_exit)

        # 使用水平布局和弹性空间，使按钮布局在水平方向上居中显示
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addLayout(btn_layout)
        btn_container.addStretch()

        right_layout.addLayout(btn_container)

        # 初始化摄像头相关变量，初始时摄像头未打开，cap为None
        self.cap = None
        # 创建一个定时器对象，用于定时更新摄像头画面
        self.timer = QTimer()
        # 将定时器的超时信号连接到update_frame方法，当定时器超时时会自动调用该方法更新画面
        self.timer.timeout.connect(self.update_frame)

        # 加载人脸检测器相关设置
        cascade_path = os.path.join('XML', 'haarcascade_frontalface_default.xml')
        # 检查人脸检测器文件是否存在，如果不存在则弹出错误提示框并终止程序
        if not os.path.exists(cascade_path):
            QMessageBox.critical(self, "错误", f"无法找到人脸检测器文件: {cascade_path}")
            sys.exit(1)

        # 使用OpenCV的CascadeClassifier加载人脸检测器文件，如果加载失败（文件可能损坏等原因），弹出错误提示框并终止程序
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            QMessageBox.critical(self, "错误", "无法加载人脸检测器文件，请检查XML文件路径！")
            sys.exit(1)

        # 初始化串口相关设置
        self.serial = QSerialPort()
        # 设置串口名称，这里默认设置为"COM3"，实际使用时需要根据实际连接的串口进行修改
        self.serial.setPortName("COM3")
        # 设置串口波特率为115200
        self.serial.setBaudRate(QSerialPort.Baud115200)
        # 设置数据位为8位
        self.serial.setDataBits(QSerialPort.Data8)
        # 设置无奇偶校验
        self.serial.setParity(QSerialPort.NoParity)
        # 设置停止位为1位
        self.serial.setStopBits(QSerialPort.OneStop)
        # 设置无流控制
        self.serial.setFlowControl(QSerialPort.NoFlowControl)
        # 尝试打开串口，如果打开失败则弹出警告提示框告知用户检查串口配置
        if not self.serial.open(QtCore.QIODevice.ReadWrite):
            QMessageBox.warning(self, "警告", "无法打开串口，请检查串口配置！")

        # 绑定按钮的点击事件与对应的方法
        self.pushButton_exit.clicked.connect(self.close)
        self.pushButton_submit.clicked.connect(self.on_submit_clicked)
        self.pushButton_open_cam.clicked.connect(self.open_camera)
        self.pushButton_close_cam.clicked.connect(self.close_camera)
        self.pushButton_recognize.clicked.connect(self.on_recognize_clicked)

        self.detected_face = None

    def closeEvent(self, event):
        """
        重写窗口关闭事件方法，在窗口关闭时进行资源释放操作。

        参数:
        - event: 关闭事件对象，用于控制关闭事件的接受或忽略等操作。

        如果摄像头已打开，释放摄像头资源；如果串口已打开，关闭串口。然后接受关闭事件，使窗口正常关闭。
        """
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        if self.serial.isOpen():
            self.serial.close()
        event.accept()

    def open_camera(self):
        """
        用于打开摄像头的方法。

        如果摄像头未打开（self.cap为None或者未处于打开状态），尝试打开摄像头（通过cv2.VideoCapture(0)，0表示默认摄像头设备）。
        如果打开失败，弹出错误提示框告知用户无法打开摄像头，并将self.cap设置为None。
        如果打开成功，启动定时器，每30毫秒触发一次update_frame方法来更新摄像头画面。
        """
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "错误", "无法打开摄像头")
                self.cap = None
                return
        self.timer.start(30)  # 每30ms更新一次画面

    def close_camera(self):
        """
        用于关闭摄像头的方法。

        如果摄像头已打开，停止定时器以停止画面更新，释放摄像头资源，并将self.cap设置为None。
        同时清空摄像头显示标签的内容，并将检测到的人脸图像设置为None。
        """
        if self.cap is not None and self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
            self.cap = None
        self.cameraLabel.clear()
        self.detected_face = None

    def update_frame(self):
        """
        用于更新摄像头画面显示以及检测画面中的人脸的方法。

        如果摄像头已打开且处于可读状态，读取一帧图像，进行如下操作：
        1. 将图像转换为灰度图，方便后续人脸检测操作。
        2. 使用加载的人脸检测器在灰度图中检测人脸，得到人脸的位置信息（坐标、宽度、高度等）。
        3. 遍历检测到的人脸，在原始彩色图像上绘制绿色矩形框标记人脸区域，只取第一张人脸作为后续处理的对象（break跳出循环），并将这张人脸的图像区域保存到self.detected_face变量中。
        4. 将图像从BGR颜色空间转换为RGB颜色空间（因为后续使用的face_recognition库通常要求RGB格式图像）。
        5. 根据图像的形状信息创建Qt的QImage对象，再将其转换为QPixmap对象，最后设置到摄像头显示标签上，实现画面更新显示。
        """
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                return

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            self.detected_face = None
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                face_roi = frame[y:y + h, x:x + w]
                self.detected_face = face_roi
                break  # 只处理第一张人脸

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qimg = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(qimg)
            self.cameraLabel.setPixmap(pixmap)

    def on_submit_clicked(self):
        """
        处理“提交”按钮点击事件的方法，用于将输入的学号、姓名以及对应的人脸特征编码保存到数据库中，
        在保存前会进行一系列的输入合法性校验以及人脸检测相关的校验。
        """
        # 获取输入框中学号文本并去除两端空白字符
        id_val = self.lineEdit_id.text().strip()
        # 获取输入框中姓名文本并去除两端空白字符
        name_val = self.lineEdit_name.text().strip()

        # 输入校验
        # 检查学号是否为空，如果为空则弹出警告提示框告知用户学号不能为空，并结束当前方法，不进行后续保存操作
        if not id_val:
            QMessageBox.warning(self, "输入错误", "学号不能为空！")
            return
        # 检查姓名是否为空，如果为空则弹出警告提示框告知用户姓名不能为空，并结束当前方法，不进行后续保存操作
        if not name_val:
            QMessageBox.warning(self, "输入错误", "姓名不能为空！")
            return

        # 检查学号是否全部由数字组成，如果不是则弹出警告提示框告知用户学号必须是数字，并结束当前方法
        if not id_val.isdigit():
            QMessageBox.warning(self, "输入错误", "学号必须是数字！")
            return
        # 检查姓名去除空格后是否全部由字母组成，如果不是则弹出警告提示框告知用户姓名必须是字母，并结束当前方法
        if not name_val.replace(' ', '').isalpha():
            QMessageBox.warning(self, "输入错误", "姓名必须是字母！")
            return

        # 调用facesql的record_exists方法检查数据库中是否已存在相同学号或姓名的记录，
        # 如果存在则弹出警告提示框告知用户该学号或姓名已存在，请更换，并结束当前方法
        if self.facesql.record_exists(id_val, name_val):
            QMessageBox.warning(self, "重复错误", "该学号或姓名已存在，请更换！")
            return

        # 检查是否检测到人脸，如果没有检测到人脸（self.detected_face为None），
        # 则弹出警告提示框告知用户未检测到人脸，请确保摄像头已开启并有正确的人脸图像，并结束当前方法
        if self.detected_face is None:
            QMessageBox.warning(self, "警告", "未检测到人脸，请确保摄像头已开启并有正确的人脸图像。")
            return

        # 提取人脸特征编码相关操作
        # 将检测到的人脸图像（BGR格式）转换为RGB格式，因为后续的face_recognition库通常要求输入的图像为RGB格式
        rgb_face = cv2.cvtColor(self.detected_face, cv2.COLOR_BGR2RGB)
        # 使用face_recognition库的face_encodings方法提取人脸的特征编码，返回一个包含特征编码的列表（可能包含多个人脸的编码，这里只处理检测到的第一个人脸）
        face_encs = face_recognition.face_encodings(rgb_face)
        # 如果没有成功提取到人脸特征编码（列表为空），则弹出警告提示框告知用户无法提取人脸特征，请重试，并结束当前方法
        if len(face_encs) == 0:
            QMessageBox.warning(self, "错误", "无法提取人脸特征，请重试。")
            return
        # 取提取到的第一个（也是唯一处理的）人脸特征编码
        face_encoding = face_encs[0]

        # 将编码存入数据库相关操作
        try:
            # 调用facetools的add_Face方法，将提取到的人脸特征编码以及学号、姓名信息保存到数据库中
            self.facetools.add_Face(face_encoding, id_val, name_val)
            # 如果保存成功，弹出信息提示框告知用户人脸数据已成功保存到数据库！
            QMessageBox.information(self, "成功", "人脸数据已成功保存到数据库！")
            # 调用clear_inputs方法清空学号、姓名输入框以及重置检测到的人脸图像相关变量
            self.clear_inputs()
        except Exception as e:
            # 如果保存过程出现异常，弹出错误提示框显示具体的错误信息（数据插入失败的原因）
            QMessageBox.critical(self, "错误", f"数据插入失败：{e}")

    def on_recognize_clicked(self):
        """
        处理“识别”按钮点击事件的方法，用于识别当前摄像头画面中检测到的人脸是否在数据库中存在匹配记录，
        若匹配成功会发送相应的串口信号。
        """
        # 检查是否检测到人脸，如果没有检测到人脸（self.detected_face为None），
        # 则弹出警告提示框告知用户未检测到人脸，请开启摄像头并确保有面部出现在摄像头前，并结束当前方法
        if self.detected_face is None:
            QMessageBox.warning(self, "警告", "未检测到人脸，请开启摄像头并确保有面部出现在摄像头前。")
            return

        # 提取当前人脸特征编码相关操作
        # 将检测到的人脸图像（BGR格式）转换为RGB格式，以满足后续face_recognition库的要求
        rgb_face = cv2.cvtColor(self.detected_face, cv2.COLOR_BGR2RGB)
        # 使用face_recognition库的face_encodings方法提取当前人脸的特征编码，返回一个包含特征编码的列表（这里只处理第一个人脸的编码）
        face_encs = face_recognition.face_encodings(rgb_face)
        # 如果没有成功提取到人脸特征编码（列表为空），则弹出警告提示框告知用户无法提取人脸特征，请重试，并结束当前方法
        if len(face_encs) == 0:
            QMessageBox.warning(self, "错误", "无法提取人脸特征，请重试。")
            return
        # 获取当前人脸的特征编码
        current_face_encoding = face_encs[0]

        # 从数据库加载所有人脸特征相关操作
        # 调用facetools的load_faceofdatabase方法从数据库中加载所有人脸数据，包括学号、姓名以及对应的人脸特征编码
        face_ids, face_names, face_encodings = self.facetools.load_faceofdatabase()
        # 如果数据库中没有人脸数据（加载的学号列表为空），则弹出提示框告知用户数据库中暂无人脸数据，并结束当前方法
        if not face_ids:
            QMessageBox.warning(self, "提示", "数据库中暂无人脸数据。")
            return

        # 使用 face_recognition 进行比较相关操作
        # 使用face_recognition库的compare_faces方法比较当前人脸特征编码与数据库中所有人脸特征编码，
        # tolerance参数设置比较的容忍度，返回一个布尔列表，表示是否匹配，每个元素对应数据库中的一条人脸记录
        matches = face_recognition.compare_faces(face_encodings, current_face_encoding, tolerance=0.6)
        # 使用face_recognition库的face_distance方法计算当前人脸特征编码与数据库中所有人脸特征编码的距离，
        # 距离越小表示越相似，返回一个距离值列表，每个元素对应数据库中的一条人脸记录
        face_distances = face_recognition.face_distance(face_encodings, current_face_encoding)

        # 如果距离列表为空（可能由于数据库中没有有效数据等原因），则弹出识别结果提示框告知用户未匹配到已知人脸，并结束当前方法
        if len(face_distances) == 0:
            QMessageBox.information(self, "识别结果", "未匹配到已知人脸。")
            return

        # 找到距离最小的匹配索引，即找到与当前人脸最相似的数据库中的人脸记录索引
        best_match_index = np.argmin(face_distances)
        # 如果该索引对应的匹配结果为True，表示找到了匹配的人脸
        if matches[best_match_index]:
            # 获取匹配到的人脸的学号
            matched_id = face_ids[best_match_index]
            # 获取匹配到的人脸的姓名
            matched_name = face_names[best_match_index]
            # 弹出信息提示框告知用户识别到的学号和姓名
            QMessageBox.information(self, "识别结果", f"识别到学号 {matched_id} 的人脸：{matched_name}")
            # 调用sendOpenSignal方法发送串口信号（可能用于后续如开门等相关操作）
            self.sendOpenSignal()
        else:
            # 如果没有匹配到已知人脸，则弹出识别结果提示框告知用户未匹配到已知人脸
            QMessageBox.information(self, "识别结果", "未匹配到已知人脸。")

    def sendOpenSignal(self):
        """
        用于发送串口信号的方法，当识别到人脸与数据库中记录匹配时调用，
        向串口发送特定数据（这里是字节类型的"open"），前提是串口处于打开状态。
        """
        if self.serial.isOpen():
            # 定义要发送的数据为字节类型的"open"，具体含义可能根据实际连接的设备而定，比如可能用于控制门锁打开等操作
            data = b"open"
            # 通过串口发送数据
            self.serial.write(data)
            # 刷新串口缓冲区，确保数据立即发送出去
            self.serial.flush()
        else:
            # 如果串口未打开，弹出警告提示框告知用户串口未打开，无法发送开锁指令！
            QMessageBox.warning(self, "警告", "串口未打开，无法发送开锁指令！")

    def clear_inputs(self):
        """
        用于清空输入框内容以及重置检测到的人脸图像相关变量的方法，
        通常在数据保存成功等操作后调用，以方便用户进行下一次操作。
        """
        # 清空学号输入框内容
        self.lineEdit_id.clear()
        # 清空姓名输入框内容
        self.lineEdit_name.clear()
        # 将检测到的人脸图像相关变量设置为None，重置状态
        self.detected_face = None

if __name__ == "__main__":
    # 确保XML文件夹存在，并包含haarcascade_frontalface_default.xml文件，
    # 如果不存在该文件，则打印提示信息告知用户缺少该文件，并结束程序
    if not os.path.exists('XML/haarcascade_frontalface_default.xml'):
        print("缺少haarcascade_frontalface_default.xml文件，请将其放在XML文件夹中。")
        sys.exit(1)
    # 设置Qt应用程序支持高DPI缩放，使得在高分辨率屏幕下界面显示更合理
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
