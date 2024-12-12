# 基于人脸识别的门禁系统（PyQt版本）

## 成员介绍
曲阜师范大学2022级物联网工程班就业指导组实训作品，成员：宋宝坤、黄伟健、李君豪、徐保森、陈泽鑫、陈振鑫、杨哲、尹济川、钟洪铭

## 简介

本项目是一个使用 Python 编写的示例程序，结合了人脸识别（face_recognition）、MySQL 数据库存储，以及通过串口（QSerialPort）向下位机发送指令实现开锁的完整功能。项目使用 PyQt5 搭建图形界面，OpenCV 负责摄像头图像处理和人脸检测，face_recognition 用于人脸特征提取和比对。用户可通过界面录入学号和姓名并进行人脸注册，后续使用摄像头对进出人员的人脸进行识别，若数据库中存在匹配的记录，则向串口发送“open”命令，实现开锁功能。

## 功能特性

- **人脸注册**：输入学号、姓名后，对当前摄像头前的人脸进行特征提取，并将学号、姓名和人脸编码存入数据库。
- **人脸识别**：对摄像头捕获的人脸进行特征提取，与数据库中已存的人脸特征进行比对，若匹配成功则显示学号姓名并通过串口向下位机发送开锁指令。
- **串口通信**：在识别成功后自动向串口发送 `"open"` 指令，供下位机执行实际的开锁动作。
- **图形界面**：基于 PyQt5 的界面，包括学号姓名输入框、摄像头图像预览窗口和各类控制按钮。

## 环境要求

### 软件依赖

- Python 3.x
- PyQt5
- OpenCV (opencv-python)
- face_recognition
- PyMySQL
- QtSerialPort (随 PyQt5 一同安装)

安装示例（请根据实际环境自行调整）：
```bash
pip install PyQt5 opencv-python face_recognition PyMySQL
```
## 数据库准备
确保在 MySQL 中创建相应的数据库和表。示例：
```bash
CREATE DATABASE db CHARSET utf8mb4;

USE db;

CREATE TABLE `face` (
    `face_number` INT AUTO_INCREMENT PRIMARY KEY,
    `id` VARCHAR(20) NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `encoding` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
## 项目代码结构概述
所有类定义和逻辑集中在 `main.py` 中（或在其他模块中引入）。主要类和模块如下：
- `FaceSQL`：负责数据库操作（插入数据、查询数据、判断记录是否存在、加载所有人脸数据）。
- `FaceTools`：负责人脸编码数据的序列化和反序列化，以及将提取到的人脸特征插入数据库。
- `MyWindow`：GUI主窗口类，负责界面布局、按钮事件处理、摄像头图像更新、用户交互以及人脸识别流程的统筹。
## 类介绍和实现原理
### FaceSQL 类
#### 定位与职责：
`FaceSQL` 类封装了与 MySQL 数据库进行交互的逻辑，包括插入新的人脸数据记录、检查记录是否存在、查询所有人脸数据等。将数据库操作逻辑集中在该类中，有利于代码维护和扩展。
#### 实现原理：
- 使用 `pymysql` 连接数据库，在构造函数中建立连接。
- `processFaceData` 方法执行通用 SQL 语句，并处理事务提交或回滚。
- `saveFaceData` 方法将学号、姓名与编码数据插入数据库。
- `allFaceData` 方法查询数据库中所有已存的人脸记录（id、name、encoding）。
- `record_exists` 方法根据学号、姓名检查数据库中是否已存在对应的记录。
### FaceTools 类
#### 定位与职责：
`FaceTools` 主要用于处理人脸特征编码的数据格式转换和存储逻辑。`face_recognition` 返回的人脸编码为 `numpy` 数组，存入数据库需序列化为字符串，从数据库取出后需反序列化为 `numpy` 数组。
#### 实现原理：
- `encoding_FaceStr` 将 `numpy` 数组的特征编码转换为用逗号分隔的字符串存储形式。
- `decoding_FaceStr` 从数据库中取出的字符串再分解为浮点数列表，最终还原为 `numpy` 数组。
- `add_Face` 调用 `FaceSQL` 的 `saveFaceData` 将新的人脸特征连同学号、姓名存入数据库。
- `load_faceofdatabase` 从数据库中加载所有已存的人脸特征数据，并解码为可比对的 `numpy` 数组列表。
### MyWindow 类
#### 定位与职责：
`MyWindow` 是整个应用程序的界面类，继承自 `QMainWindow`。它负责：
- 构建图形用户界面：输入表单、摄像头显示区域、控制按钮等布局与样式。
- 处理用户操作（按钮点击事件）：提交人脸数据、开启/关闭摄像头、执行人脸识别、退出程序。
- 使用定时器 `QTimer` 轮询摄像头帧，并将图像数据显示在界面中。
- 使用 `face_recognition` 提取人脸特征编码，与数据库中已存数据比对匹配。
- 识别成功后，调用串口发送“open”指令，实现门禁开锁逻辑。
#### 实现原理：

1.界面布局：
在构造函数中创建主窗口控件及布局：
- 左侧为摄像头显示区域 `cameraLabel`。
- 右侧为学号、姓名输入行，提交、识别、开启/关闭摄像头、退出等按钮。
2.摄像头图像获取与显示：
使用 `cv2.VideoCapture(0)` 打开摄像头。启动 `QTimer` 定时器周期调用 `update_frame` 方法：
- `update_frame` 方法从摄像头读取图像，将其转换为 `RGB` 格式，再用 `QImage`、`QPixmap` 更新到 `cameraLabel` 中。
- 同时使用 `face_cascade` 对图像中的人脸进行检测，如果检测到则在图像中绘制矩形框，并将检测到的人脸区域暂存供后续使用（提交人脸数据或进行识别）。
3.人脸注册（on_submit_clicked）：
当用户点击“提交”按钮：
- 校验学号和姓名输入格式。
- 确保摄像头中已检测到人脸。
- 使用 `face_recognition.face_encodings` 提取人脸特征，调用 `FaceTools.add_Face` 存入数据库。
- 显示成功提示。
4.人脸识别（on_recognize_clicked）：
当用户点击“识别”按钮：
- 确保摄像头中已检测到人脸。
- 提取该人脸特征，使用 `FaceTools.load_faceofdatabase` 加载所有已存人脸数据。
- 使用 `face_recognition.compare_faces` 和 `face_recognition.face_distance` 比对特征，找到最匹配的人脸。
- 若匹配成功：显示学号和姓名提示信息，同时调用 `sendOpenSignal()` 通过串口发送“open”指令实现开锁。
5.串口控制（sendOpenSignal）：
若串口已打开，则向串口发送“open”字节数据，并刷新缓冲区。若串口未打开，则提示警告信息。

### 整体工作流程
1.程序启动后，主界面初始化但摄像头未开启。

2.用户点击“开启摄像头”按钮时，程序打开摄像头（0号设备），开始通过定时器轮询显示图像，并检测人脸。

3.用户在输入框中输入学号、姓名后点击“提交”时，程序从当前帧中获取人脸特征，将学号、姓名和特征编码存入数据库，并弹出“人脸数据已成功保存”。 

4.当用户点击“识别”时，程序从当前画面中提取人脸特征，与数据库中所有已存的特征比对。若匹配成功，显示匹配到的人脸对应的学号和姓名，并通过串口发送“open”指令。弹出提示，告知“已开锁”。

5.用户可重复注册或识别操作。退出程序时，程序关闭摄像头和串口，安全退出。
