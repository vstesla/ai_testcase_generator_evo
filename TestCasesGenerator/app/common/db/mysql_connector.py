# import pymysql
# import os
# import logging
# from pymysql.cursors import DictCursor

# logger = logging.getLogger(__name__)

# class MySQLConnector:
#     """
#     MySQL 连接管理类
#     """
#     def __init__(self):
#         self.host = os.getenv("DB_HOST", "localhost")
#         self.port = int(os.getenv("DB_PORT", 3306))
#         self.user = os.getenv("DB_USER", "root")
#         self.password = os.getenv("DB_PASSWORD", "")
#         self.database = os.getenv("DB_NAME", "test_cases_db")
#         self.charset = "utf8mb4"

#     def get_connection(self):
#         """
#         获取数据库连接
#         """
#         try:
#             conn = pymysql.connect(
#                 host=self.host,
#                 port=self.port,
#                 user=self.user,
#                 password=self.password,
#                 database=self.database,
#                 charset=self.charset,
#                 cursorclass=DictCursor,
#                 autocommit=False  # 手动提交事务
#             )
#             return conn
#         except Exception as e:
#             logger.error(f"Failed to connect to MySQL: {e}")
#             raise

# # 全局连接器实例
# mysql_connector = MySQLConnector()
import pymysql
from typing import List, Dict, Any, Optional, Tuple
from queue import Queue
from threading import Lock


class ConnectionPool:
    """数据库连接池实现"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str,
                 max_connections: int = 20, min_idle_connections: int = 5, max_idle_time: int = 300, charset: str = "utf8mb4"):
        """
        初始化连接池

        Args:
            host (str): 数据库主机地址
            port (int): 数据库端口
            user (str): 数据库用户名
            password (str): 数据库密码
            database (str): 数据库名称
            max_connections (int): 最大连接数
            max_idle_time (int): 最大空闲时间(秒)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.charset = charset
        self.pool = Queue(max_connections)
        self.min_idle_connections = min_idle_connections
        self.lock = Lock()
        self._init_pool()

    def _init_pool(self):
        """初始化连接池 - 使用极保守的懒加载策略避免启动时连接风暴"""
        # 只创建少量初始连接，避免启动时连接数过多
        successful_connections = 0

        # 极保守策略：最多创建1个初始连接，避免服务器连接数超限
        initial_connections = min(self.min_idle_connections, 1)  # 最多创建1个初始连接

        for _ in range(initial_connections):
            conn = self._create_connection()
            if conn and self._validate_connection(conn):
                self.pool.put(conn)
                successful_connections += 1

        # 剩余的连接将在需要时按需创建

    def _create_connection(self) -> Optional[pymysql.Connection]:
        """创建新连接"""
        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        except Exception as e:
            print(f"创建数据库连接失败: {e}")
            return None

    def _validate_connection(self, conn: pymysql.Connection) -> bool:
        """可靠的连接状态检查"""
        if conn is None:
            return False

        # 基础状态检查
        if not hasattr(conn, 'open') or not conn.open:
            return False

        try:
            # 执行轻量级查询验证连接
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            # print(f"数据库连接正常：{conn}")
            return True
        except (pymysql.OperationalError, pymysql.InterfaceError) as err:
            # 连接错误代码：2006(MySQL server has gone away), 2013(Lost connection)
            if err.args[0] in [2006, 2013]:
                return False
            # 其他操作错误可能不是连接问题，重新抛出
            raise
        except Exception as unexpected_err:
            # 记录未知异常，但认为连接无效
            return False

    def get_connection(self, timeout: int = 5) -> Optional[pymysql.Connection]:
        """从连接池获取可用连接"""
        import queue
        try:
            conn = self.pool.get(timeout=timeout)
            if self._validate_connection(conn):
                return conn
            else:
                new_conn = self._create_connection()
                return new_conn
        except queue.Empty:
            new_conn = self._create_connection()
            return new_conn

    def get_connection_with_retry(self, max_retries: int = 3, retry_interval: float = 1.0) -> Optional[pymysql.Connection]:
        """
        获取连接（带重试和延迟机制）

        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）

        Returns:
            Optional[pymysql.Connection]: 数据库连接
        """
        import time

        for attempt in range(max_retries):
            conn = self.get_connection()
            if conn:
                return conn

            if attempt < max_retries - 1:
                print(f"等待 {retry_interval} 秒后重试连接...")
                time.sleep(retry_interval)

        return None

    def release_connection(self, conn: pymysql.Connection):
        """释放连接回池"""
        try:
            # 首先检查连接是否仍然有效
            if conn and conn.open:
                # 执行更全面的连接验证
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                    # 如果验证通过，检查连接池是否已满
                    if self.pool.full():
                        # 连接池已满，关闭这个连接而不是放回池中
                        conn.close()
                        print("连接池已满，关闭连接")
                    else:
                        # 连接有效且池未满，放回连接池
                        self.pool.put(conn)
                except Exception as e:
                    # 连接验证失败，关闭连接
                    try:
                        conn.close()
                    except Exception:
                        pass
            else:
                # 连接已经关闭或无效，直接关闭
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception as e:
            print(f"")


class MySQLConnector:
    """MySQL数据库连接工具类"""

    def __init__(self, pool: ConnectionPool):
        """
        初始化数据库连接工具

        Args:
            pool (ConnectionPool): 连接池实例
        """
        self.pool = pool
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """从连接池获取连接"""
        self.connection = self.pool.get_connection()
        if self.connection:
            try:
                self.cursor = self.connection.cursor()
                # 验证连接是否真正有效
                try:
                    self.cursor.execute("SELECT 1")
                    return True
                except Exception as validate_error:
                    if self.connection:
                        try:
                            self.connection.close()
                        except Exception:
                            pass
                        self.connection = None
                    return False
            except Exception as e:
                if self.connection:
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                    self.connection = None
                return False
        else:
            # 获取数据库名称
            db_name = getattr(self.pool, 'database', 'unknown')
            return False

    def _check_connection(self) -> bool:
        """检查连接是否有效"""
        if not self.connection:
            # 尝试获取连接
            self.connection = self.pool.get_connection()
            if not self.connection:
                return False
            try:
                self.cursor = self.connection.cursor()
            except Exception as e:
                self.pool.release_connection(self.connection)
                self.connection = None
                return False

        # 验证连接有效性
        is_valid = self.pool._validate_connection(self.connection)
        if not is_valid:
            print('')
            # 连接无效，重新获取
            if self.cursor:
                try:
                    self.cursor.close()
                except Exception:
                    pass
            if self.connection:
                try:
                    # 先释放无效连接回池，让连接池处理
                    self.pool.release_connection(self.connection)
                except Exception:
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                self.connection = None

            # 获取新连接
            self.connection = self.pool.get_connection()
            if not self.connection:
                return False
            try:
                self.cursor = self.connection.cursor()
            except Exception as e:
                self.pool.release_connection(self.connection)
                self.connection = None
                return False

        return True
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询语句"""
        if not self._check_connection():
            raise Exception("数据库连接失败")
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"查询执行失败: {e}")
            if self.connection:
                self.pool.release_connection(self.connection)
                self.connection = None
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新语句"""
        if not self._check_connection():
            raise Exception("数据库连接失败")
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"更新执行失败: {e}")
            if self.connection:
                self.connection.rollback()
                self.pool.release_connection(self.connection)
                self.connection = None
            raise

    def get_table_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取表数据

        Args:
            table_name (str): 表名
            limit (int): 限制返回记录数

        Returns:
            List[Dict[str, Any]]: 表数据
        """
        return self.execute_query(f"SELECT * FROM `{table_name}` LIMIT {limit}")

    def drop_table(self, table_name: str) -> bool:
        """
        删除数据表

        Args:
            table_name (str): 表名

        Returns:
            bool: 删除是否成功
        """
        return self.execute_update(f"DROP TABLE IF EXISTS `{table_name}`")


# 模块级别的连接池缓存
_connection_pool_instance = None


def create_tyystool_connection():
    """创建并返回数据库连接池实例"""
    global _connection_pool_instance

    # 如果已经存在连接池实例，直接返回（避免重复创建）
    if _connection_pool_instance is not None:
        return _connection_pool_instance

    import os
    import platform

    # 根据操作系统设置默认环境
    # Windows系统默认使用测试环境，Linux系统默认使用生产环境
    if platform.system().lower() == "windows":
        default_environment = "test"
    else:
        default_environment = "production"

    # 获取当前环境，使用操作系统智能默认值
    environment = os.getenv("ENVIRONMENT", default_environment)

    # 根据环境选择数据库名
    if environment.lower() in ["development", "dev", "test", "testing"]:
        database_name = "test_cases_db"  # 测试环境数据库
        # 使用环境变量标记，避免reloader导致的重复打印
        if not os.getenv("DB_ENV_INFO_PRINTED"):
            print(f"[TEST] 当前为测试环境，连接到数据库: {database_name}")
            os.environ["DB_ENV_INFO_PRINTED"] = "1"
    else:
        database_name = "test_cases_db"  # 生产环境数据库
        # 使用环境变量标记，避免reloader导致的重复打印
        if not os.getenv("DB_ENV_INFO_PRINTED"):
            print(f"[PROD] 当前为生产环境，连接到数据库: {database_name}")
            os.environ["DB_ENV_INFO_PRINTED"] = "1"

    # 使用默认配置创建连接池
    pool = ConnectionPool(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database=database_name,
        charset="utf8mb4",
        max_connections=20,  # 增加最大连接数
        min_idle_connections=5,  # 减少最小空闲连接数，避免连接风暴
        max_idle_time=300  # 增加空闲时间
    )

    # 创建MySQLConnector实例并缓存
    _connection_pool_instance = MySQLConnector(pool)
    return _connection_pool_instance
          
    