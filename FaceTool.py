import numpy as np

# 定义一个名为FaceTools的类，用于处理面部相关的工具方法，它依赖于FaceSQL类来与数据库进行交互
class FaceTools:
    def __init__(self, facesql):
        """
        类的构造函数，用于初始化FaceTools类的实例。

        参数:
        - facesql: 一个FaceSQL类的实例，通过这个实例来调用数据库操作相关的方法，
                   以此实现FaceTools类中与数据库交互的功能。
        """
        self.facesql = facesql

    def encoding_FaceStr(self, image_face_encoding):
        """
        将面部特征编码（一般是numpy数组形式）转换为字符串表示形式。

        参数:
        - image_face_encoding: 以numpy数组形式表示的面部特征编码，例如通过人脸识别算法得到的特征向量。

        先将numpy数组转换为列表，再使用map函数将列表中的每个元素转换为字符串形式，
        最后使用逗号将这些字符串连接起来，形成一个可以方便存储在数据库中的字符串表示形式。
        返回转换后的字符串。
        """
        return ','.join(map(str, image_face_encoding.tolist()))

    def decoding_FaceStr(self, encoding_str):
        """
        将存储在数据库中的面部特征编码字符串还原为numpy数组形式。

        参数:
        - encoding_str: 从数据库中读取出来的面部特征编码字符串，格式是由encoding_FaceStr方法生成的，
                        即逗号分隔的数值字符串形式。

        首先去除字符串两端可能存在的空白字符，然后按照逗号进行分割，得到一个字符串列表。
        接着使用map函数将字符串列表中的每个元素转换为浮点数，最后将这些浮点数组成的列表转换为numpy数组，
        并返回该numpy数组，也就是还原后的面部特征编码。
        """
        dlist = encoding_str.strip().split(',')
        dfloat = list(map(float, dlist))
        face_encoding = np.array(dfloat)
        return face_encoding

    def add_Face(self, image_face_encoding, id_val, name_val):
        """
        将给定的面部特征编码以及对应的标识、名称添加到数据库中。

        参数:
        - image_face_encoding: 要添加的面部特征编码，以numpy数组形式表示。
        - id_val: 该面部数据记录在数据库中的唯一标识符，例如编号等。
        - name_val: 与该面部数据相关联的名称，比如人物姓名等。

        首先调用encoding_FaceStr方法将面部特征编码转换为字符串形式，
        然后通过self.facesql实例（即FaceSQL类的实例）调用其saveFaceData方法，
        将转换后的编码字符串以及对应的标识和名称保存到数据库中。
        """
        encoding_str = self.encoding_FaceStr(image_face_encoding)
        self.facesql.saveFaceData(id_val, name_val, encoding_str)

    def load_faceofdatabase(self):
        """
        从数据库中加载所有的面部数据，包括面部标识、名称以及特征编码。

        返回值:
        返回三个列表，分别包含面部数据记录的标识（face_ids）、名称（face_names）以及还原后的面部特征编码（face_encodings）。

        首先初始化三个空列表，用于存储后续从数据库中读取的数据。
        尝试通过self.facesql实例调用allFaceData方法获取数据库中所有的面部数据记录。
        对于每一条记录，分别提取出标识、名称以及编码字符串，将标识和名称添加到对应的列表中，
        并调用decoding_FaceStr方法将编码字符串还原为numpy数组后添加到面部特征编码列表中。
        如果在加载过程中出现异常，将打印错误信息，最后返回这三个列表（即使加载失败，返回的列表可能为空）。
        """
        face_ids = []
        face_names = []
        face_encodings = []
        try:
            face_data = self.facesql.allFaceData()
            for row in face_data:
                face_id, face_name, encoding_str = row
                face_ids.append(face_id)
                face_names.append(face_name)
                face_encodings.append(self.decoding_FaceStr(encoding_str))
        except Exception as e:
            print(f"加载数据库人脸数据失败: {e}")
        return face_ids, face_names, face_encodings