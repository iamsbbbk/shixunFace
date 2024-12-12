import sys
import pymysql

# 定义一个名为FaceSQL的类，用于操作与面部数据相关的数据库操作
class FaceSQL:
    def __init__(self):
        """
        类的构造函数，用于初始化数据库连接和设置相关属性。

        尝试建立与MySQL数据库的连接，连接的相关参数包括主机地址、用户名、密码、数据库名称、字符编码以及端口号。
        如果连接过程中出现异常，将打印错误信息并终止程序（通过sys.exit(1)）。
        同时初始化要操作的表名，这里默认为'face'表。
        """
        try:
            # 使用pymysql库建立与MySQL数据库的连接
            self.conn = pymysql.connect(
                host="127.0.0.1",
                user="root",
                password="cekay383",
                db="db",
                charset="utf8mb4",
                port=3306
            )
            # 设置要操作的表名，初始化为'face'表，后续的数据库操作基本围绕此表展开
            self.table_name = 'face'
        except Exception as e:
            # 如果连接数据库出现异常，打印出详细的错误信息
            print(f"数据库连接错误: {e}")
            # 终止程序，返回状态码1表示出现错误
            sys.exit(1)

    def processFaceData(self, sqlstr, args=()):
        """
        用于执行给定的SQL语句的通用方法。

        参数:
        - sqlstr: 要执行的SQL语句字符串。
        - args: SQL语句中占位符对应的参数元组，默认为空元组。

        此方法首先会打印出即将执行的SQL语句以及对应的参数，方便调试查看。
        然后获取数据库游标对象，尝试执行SQL语句并提交事务。
        如果执行过程中出现异常，将回滚事务以保证数据一致性，并打印出错误信息。
        无论执行成功与否，最后都会关闭游标。
        """
        # 打印即将执行的SQL语句以及对应的参数，方便调试时查看执行情况
        print(f"Executing SQL: {sqlstr} | Args: {args}")
        cursor = self.conn.cursor()
        try:
            # 使用游标执行SQL语句，传入参数（如果有）
            cursor.execute(sqlstr, args)
            # 提交事务，使数据库的修改生效（例如插入、更新等操作）
            self.conn.commit()
        except Exception as e:
            # 如果执行SQL语句出现异常，回滚事务，撤销当前事务中对数据库的所有修改操作
            self.conn.rollback()
            print(f"执行SQL失败: {e}")
        finally:
            # 关闭游标，释放资源
            cursor.close()

    def saveFaceData(self, id_val, name_val, encoding_str):
        """
        用于向数据库中保存面部数据的方法。

        参数:
        - id_val: 面部数据记录的唯一标识符值。
        - name_val: 与面部数据相关联的名称值。
        - encoding_str: 面部特征编码的字符串表示形式。

        调用processFaceData方法，传入插入数据的SQL语句以及对应的数据值，
        将包含id、name、encoding三个字段的数据插入到指定的表（self.table_name）中。
        """
        self.processFaceData(
            f"INSERT INTO {self.table_name}(id, name, encoding) VALUES (%s, %s, %s)",
            (id_val, name_val, encoding_str)
        )

    def allFaceData(self):
        """
        用于获取数据库中所有面部数据记录的方法。

        首先获取数据库游标对象，然后执行查询语句，从指定表（self.table_name）中获取所有的id、name、encoding字段数据。
        如果查询执行成功，将获取到的所有结果返回；如果出现异常，会回滚事务以保证数据一致性，打印错误信息，并返回一个空列表。
        最后关闭游标释放资源。
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"SELECT id, name, encoding FROM {self.table_name}")
            result = cursor.fetchall()
            return result
        except Exception as e:
            self.conn.rollback()
            print(f"执行SQL失败: {e}")
            return []
        finally:
            cursor.close()

    def record_exists(self, id_val, name_val):
        """
        用于检查数据库中是否存在指定id或name的面部数据记录的方法。

        参数:
        - id_val: 要检查的面部数据记录的唯一标识符值。
        - name_val: 要检查的与面部数据相关联的名称值。

        构造一个查询语句，通过COUNT(*)统计符合条件（id等于给定值或者name等于给定值）的记录数量。
        获取数据库游标对象并执行该查询语句，获取查询结果中的计数值（第一条记录的第一个字段值），
        判断该计数值是否大于0来确定是否存在对应的记录。
        如果执行过程中出现异常，打印错误信息并返回False表示检查失败。
        最后关闭游标释放资源。
        """
        sql = f"SELECT COUNT(*) FROM {self.table_name} WHERE id = %s OR name = %s"
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, (id_val, name_val))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"执行SQL失败: {e}")
            return False
        finally:
            cursor.close()