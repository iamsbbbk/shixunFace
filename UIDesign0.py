# -*- coding: utf-8 -*-

import sys
import cv2
import pymysql
import numpy as np
import face_recognition
import os
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QLabel, QVBoxLayout,
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton
)
from PyQt5.QtCore import QTimer, Qt
import pymysql.cursors

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class FaceSQL:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="127.0.0.1",        # 修改为您的数据库IP地址
                user="root",             # 修改为您的数据库用户名
                password="cekay383",     # 修改为您的数据库密码
                db="db",                 # 修改为您的数据库名称
                charset="utf8mb4",
                port=3306,
                cursorclass=pymysql.cursors.DictCursor  # 使用字典游标，便于数据处理
            )
            self.table_name = 'face'
            logging.info("成功连接到数据库")
        except Exception as e:
            logging.error(f"数据库连接错误: {e}")
            sys.exit(1)

    def processFaceData(self, sqlstr, args=()):
        logging.debug(f"Executing SQL: {sqlstr} | Args: {args}")
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sqlstr, args)
                self.conn.commit()
                logging.debug("SQL执行成功")
            except Exception as e:
                self.conn.rollback()
                logging.error(f"执行SQL失败: {e}")

    def saveFaceData(self, id, name, encoding_array):
        encoding_bytes = encoding_array.tobytes()  # 转换为二进制
        logging.debug(f"Encoding bytes type: {type(encoding_bytes)}, length: {len(encoding_bytes)}")
        self.processFaceData(
            f"INSERT INTO {self.table_name}(id, name, encoding) VALUES (%s, %s, %s)",
            (id, name, pymysql.Binary(encoding_bytes))
        )

    def updateFaceData(self, id, name, encoding_array):
        encoding_bytes = encoding_array.tobytes()
        logging.debug(f"Updating encoding bytes type: {type(encoding_bytes)}, length: {len(encoding_bytes)}")
        self.processFaceData(
            f"UPDATE {self.table_name} SET name = %s, encoding = %s WHERE id = %s",
            (name, pymysql.Binary(encoding_bytes), id)
        )

    def execute_float_sqlstr(self, sqlstr):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sqlstr)
                results = cursor.fetchall()
                logging.debug(f"SQL查询成功，结果数: {len(results)}")
                return results
            except Exception as e:
                self.conn.rollback()
                logging.error(f"执行SQL失败: {e}")
                return []

    def searchFaceData(self, id):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", (id,))
                result = cursor.fetchall()
                logging.debug(f"搜索到{len(result)}条记录")
                return result
            except Exception as e:
                self.conn.rollback()
                logging.error(f"执行SQL失败: {e}")
                return []

    def allFaceData(self):
        return self.execute_float_sqlstr(f"SELECT id, name, encoding FROM {self.table_name}")

    def record_exists(self, id_val, name_val):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(f"SELECT COUNT(*) AS count FROM {self.table_name} WHERE id = %s OR name = %s", (id_val, name_val))
                result = cursor.fetchone()
                count = result['count']
                logging.debug(f"记录存在检查，计数: {count}")
                return count > 0
            except Exception as e:
                logging.error(f"执行SQL失败: {e}")
                return False


class FaceTools:
    def __init__(self, facesql):
        self.facesql = facesql

    def add_Face(self, image_face_encoding, id, name):
        self.facesql.saveFaceData(id, name, image_face_encoding)

    def update_Face(self, image_face_encoding, id, name):
        self.facesql.updateFaceData(id, name, image_face_encoding)

    def load_faceofdatabase(self):
        face_ids = []
        face_names = []
        face_encodings = []
        try:
            face_data = self.facesql.allFaceData()
            for row in face_data:
                face_id = row['id']
                face_name = row['name']
                encoding_bytes = row['encoding']
                logging.debug(f"Retrieved encoding bytes for ID {face_id}: type={type(encoding_bytes)}, length={len(encoding_bytes)}")
                face_ids.append(face_id)
                face_names.append(face_name)
                # 假设 face_recognition 使用 float64
                face_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
                face_encodings.append(face_encoding)
            logging.info(f"加载数据库中{len(face_ids)}个人脸数据")
        except Exception as e:
            logging.error(f"加载数据库人脸数据失败: {e}")
        return face_ids, face_names, face_encodings


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()

        self.setWindowTitle("人脸识别系统")
        self.resize(1000, 700)

        # 初始化数据库和人脸工具类
        self.facesql = FaceSQL()
        self.facetools = FaceTools(self.facesql)

        # 主布局
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 左侧摄像头显示区域
        self.cameraLabel = QLabel()
        self.cameraLabel.setFixedSize(640, 480)
        self.cameraLabel.setStyleSheet("border: 1px solid #ccc; background-color: #000;")
        self.cameraLabel.setScaledContents(True)
        main_layout.addWidget(self.cameraLabel)

        # 右侧控制区布局
        right_layout = QVBoxLayout()
        right_layout.setSpacing(30)
        main_layout.addLayout(right_layout)

        # 表单布局：学号(id)和姓名(name)输入
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        self.lineEdit_id = QLineEdit()
        self.lineEdit_name = QLineEdit()

        # 美化输入框
        input_style = """
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """
        self.lineEdit_id.setStyleSheet(input_style)
        self.lineEdit_name.setStyleSheet(input_style)

        form_layout.addRow("学号 (ID):", self.lineEdit_id)
        form_layout.addRow("姓名 (Name):", self.lineEdit_name)

        # 使用垂直布局和弹性空间，使表单居中
        form_container = QVBoxLayout()
        form_container.addStretch()
        form_container.addLayout(form_layout)
        form_container.addStretch()
        right_layout.addLayout(form_container)

        # 按钮区域
        self.pushButton_submit = QPushButton("提交")
        self.pushButton_recognize = QPushButton("识别")
        self.pushButton_open_cam = QPushButton("开启摄像头")
        self.pushButton_close_cam = QPushButton("关闭摄像头")
        self.pushButton_exit = QPushButton("退出")

        # 按钮样式
        button_styles = {
            self.pushButton_submit: """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                }
            """,
            self.pushButton_recognize: """
                QPushButton {
                    background-color: #FFC107;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #FFB300;
                }
                QPushButton:pressed {
                    background-color: #FFA000;
                }
            """,
            self.pushButton_open_cam: """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1e88e5;
                }
                QPushButton:pressed {
                    background-color: #1976d2;
                }
            """,
            self.pushButton_close_cam: """
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
                QPushButton:pressed {
                    background-color: #616161;
                }
            """,
            self.pushButton_exit: """
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #e53935;
                }
                QPushButton:pressed {
                    background-color: #d32f2f;
                }
            """
        }

        for btn, style in button_styles.items():
            btn.setStyleSheet(style)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addWidget(self.pushButton_submit)
        btn_layout.addWidget(self.pushButton_recognize)
        btn_layout.addWidget(self.pushButton_open_cam)
        btn_layout.addWidget(self.pushButton_close_cam)
        btn_layout.addWidget(self.pushButton_exit)

        # 按钮布局居中
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addLayout(btn_layout)
        btn_container.addStretch()

        right_layout.addLayout(btn_container)

        # 初始化摄像头
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # 加载人脸检测器
        cascade_path = os.path.join('XML', 'haarcascade_frontalface_alt2.xml')
        if not os.path.exists(cascade_path):
            QMessageBox.critical(self, "错误", f"无法找到人脸检测器文件: {cascade_path}")
            sys.exit(1)

        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            QMessageBox.critical(self, "错误", "无法加载人脸检测器文件，请检查XML文件路径！")
            sys.exit(1)

        # 绑定事件
        self.pushButton_exit.clicked.connect(self.close_window)
        self.pushButton_submit.clicked.connect(self.on_submit_clicked)
        self.pushButton_open_cam.clicked.connect(self.open_camera)
        self.pushButton_close_cam.clicked.connect(self.close_camera)
        self.pushButton_recognize.clicked.connect(self.on_recognize_clicked)

        self.detected_face = None  # 用于存储当前检测到的人脸图像数据

    def close_window(self):
        self.close()

    def open_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "错误", "无法打开摄像头")
                self.cap = None
                return
            self.timer.start(30)  # 每30ms更新一次画面
            logging.info("摄像头已开启")
        else:
            QMessageBox.information(self, "信息", "摄像头已经开启")

    def close_camera(self):
        if self.cap is not None:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            logging.info("摄像头已关闭")
        self.cameraLabel.clear()
        self.detected_face = None

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                logging.warning("无法读取摄像头画面")
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
        # 从文本框中获取输入数据
        id_val = self.lineEdit_id.text().strip()
        name_val = self.lineEdit_name.text().strip()

        # 输入校验
        if not id_val:
            QMessageBox.warning(self, "输入错误", "学号不能为空！")
            return
        if not name_val:
            QMessageBox.warning(self, "输入错误", "姓名不能为空！")
            return

        if not id_val.isdigit():
            QMessageBox.warning(self, "输入错误", "学号必须是数字！")
            return
        if not name_val.replace(' ', '').isalpha():
            QMessageBox.warning(self, "输入错误", "姓名必须是字母！")
            return

        # 检查数据库中是否已存在相同学号或姓名
        if self.facesql.record_exists(id_val, name_val):
            QMessageBox.warning(self, "重复错误", "该学号或姓名已存在，请更换！")
            return

        if self.detected_face is None:
            QMessageBox.warning(self, "警告", "未检测到人脸，请确保摄像头已开启并有正确的人脸图像。")
            return

        # 提取人脸特征编码
        rgb_face = cv2.cvtColor(self.detected_face, cv2.COLOR_BGR2RGB)
        face_encs = face_recognition.face_encodings(rgb_face)
        if len(face_encs) == 0:
            QMessageBox.warning(self, "错误", "无法提取人脸特征，请重试。")
            return
        face_encoding = face_encs[0]

        # 将编码存入数据库
        try:
            self.facetools.add_Face(face_encoding, id_val, name_val)
            QMessageBox.information(self, "成功", "人脸数据已成功保存到数据库！")
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据插入失败：{e}")

    def on_recognize_clicked(self):
        if self.detected_face is None:
            QMessageBox.warning(self, "警告", "未检测到人脸，请开启摄像头并确保有面部出现在摄像头前。")
            return

        # 提取当前人脸特征编码
        rgb_face = cv2.cvtColor(self.detected_face, cv2.COLOR_BGR2RGB)
        face_encs = face_recognition.face_encodings(rgb_face)
        if len(face_encs) == 0:
            QMessageBox.warning(self, "错误", "无法提取人脸特征，请重试。")
            return
        current_face_encoding = face_encs[0]

        # 从数据库加载所有人脸特征
        face_ids, face_names, face_encodings = self.facetools.load_faceofdatabase()
        if not face_ids:
            QMessageBox.warning(self, "提示", "数据库中暂无人脸数据。")
            return

        # 使用 face_recognition 库的比较功能
        try:
            matches = face_recognition.compare_faces(face_encodings, current_face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(face_encodings, current_face_encoding)
        except Exception as e:
            logging.error(f"人脸比较失败: {e}")
            QMessageBox.critical(self, "错误", f"人脸比较失败：{e}")
            return

        if len(face_distances) == 0:
            QMessageBox.information(self, "识别结果", "未匹配到已知人脸。")
            return

        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            matched_id = face_ids[best_match_index]
            matched_name = face_names[best_match_index]
            QMessageBox.information(self, "识别结果", f"识别到学号 {matched_id} 的人脸：{matched_name}")
        else:
            QMessageBox.information(self, "识别结果", "未匹配到已知人脸。")

    def clear_inputs(self):
        self.lineEdit_id.clear()
        self.lineEdit_name.clear()
        self.detected_face = None


if __name__ == "__main__":
    # 确保XML文件夹存在，并包含haarcascade_frontalface_alt2.xml
    cascade_file = 'XML/haarcascade_frontalface_alt2.xml'
    if not os.path.exists(cascade_file):
        print(f"缺少 {cascade_file} 文件，请将其放在XML文件夹中。")
        sys.exit(1)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
