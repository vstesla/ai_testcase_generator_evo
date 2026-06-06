import logging
from app.common.db.mysql_connector import create_tyystool_connection

logger = logging.getLogger(__name__)

class DBUtilsClass:
    """
    数据库工具类，负责执行查询和更新
    """
    def __init__(self):
        self.connector = create_tyystool_connection()

    def __call__(self):
        # 允许实例被调用以兼容 api.py 中的 DBUtils() 实例化方式
        return self

    def connect(self):
        """验证数据库连接是否可用（获取连接 → 校验 → 立即归还连接池）"""
        try:
            conn = self.connector.pool.get_connection()
            if not conn:
                return False
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            finally:
                # 无论校验成功与否，都要把连接归还连接池
                self.connector.pool.release_connection(conn)
        except Exception as e:
            logger.error(f"DB Connect check failed: {e}")
            return False

    def disconnect(self):
        """断开连接（连接已由 connect() 自动归还，此处为兼容旧调用链保留）"""
        pass

    def execute_query(self, query, params=None):
        """执行查询 (SELECT)"""
        return self.connector.execute_query(query, params)

    def execute_update(self, query, params=None):
        """执行更新/插入/删除 (INSERT, UPDATE, DELETE)"""
        return self.connector.execute_update(query, params)

    def insert(self, table, data):
        """插入数据"""
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.execute_update(sql, values)

    def update(self, table, data, where):
        """更新数据"""
        if not data:
            return 0
        if not where:
            raise ValueError("update requires a where condition")

        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        values = tuple(data.values()) + tuple(where.values())

        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        return self.execute_update(sql, values)

    def select(self, table, columns=None, where=None):
        """查询数据"""
        cols = "*" if not columns else ", ".join(columns)
        sql = f"SELECT {cols} FROM {table}"
        params = []
        
        if where:
            conditions = []
            for k, v in where.items():
                conditions.append(f"{k} = %s")
                params.append(v)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        return self.execute_query(sql, tuple(params))

# 导出一个全局实例，且名字叫 DBUtils，这样能同时兼容 cos.py 和 api.py 的两种用法
DBUtils = DBUtilsClass()
# 为了兼容 process_service.py 等地方的旧有导入 (from app.common.db.db_utils import db_utils)
db_utils = DBUtils
