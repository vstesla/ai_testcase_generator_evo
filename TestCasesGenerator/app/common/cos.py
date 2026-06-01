from io import BytesIO
import os
import boto3
from botocore.client import Config
from datetime import datetime

from app.common.db.db_utils import DBUtils as DB # 删除

serviceType = 's3'
access_key = os.getenv('COS_SECRET_ID', '')
secretKey = os.getenv('COS_SECRET_KEY', '')
endpoint = os.getenv('COS_ENDPOINT', 'https://cos.ap-guangzhou.myqcloud.com')
region = os.getenv('COS_REGION', 'ap-guangzhou')
verifyIsNot = False
bucketName = os.getenv('COS_BUCKET_NAME', 'testcasesgeneratorcos-1304137470')
addressing_style = os.getenv('COS_ADDRESSING_STYLE', 'virtual')

def file_id_generator():
    if not DB.connect():
        raise Exception("数据库连接失败")
    
    time_part = datetime.now().strftime("%Y%m%d")
    time_part = str(time_part)

    col = DB.execute_query(f"select * from file_common_table fct where file_id like '{time_part}%' order by file_id desc")
    DB.disconnect()

    if not col:
        num_part = '0001'
    else:
        num_part = str(int(col[0]['file_id'][-4:]) + 1)
        num_part = num_part.zfill(4)
    file_id = time_part + num_part
    return file_id

class ObjectStorage:

    def __init__(self):
        self.client = boto3.client(
            serviceType,
            aws_access_key_id=access_key,
            aws_secret_access_key=secretKey,
            endpoint_url=endpoint,
            region_name=region,
            verify=verifyIsNot,
            config=Config(signature_version='s3v4', s3={'addressing_style': addressing_style})
        )

    def upload_file(self,upload_file_path: str, storage_path: str,user_id: str, user_name: str) -> str:
        """
        上传本地文件到 COS

        Args:
            upload_file_path (str): 本地文件路径
            storage_path (str): COS 存储路径
            user_id (str): 用户 ID
            user_name (str): 用户名

        Returns:
            str: 生成的文件ID

        Raises:
            Exception: 文件不存在，数据库连接失败或上传失败时抛出异常
        """
        if not DB.connect():
            raise Exception("数据库连接失败")
        
        storage_path_l = storage_path.replace("\\","/")
        storage_path_l = storage_path_l.split("/")
        file_source = storage_path_l[0]
        skill_description = storage_path_l[1]
        file_path = "/".join(storage_path_l[2:-1])
        file_name = storage_path_l[-1]
        file_id = file_id_generator()

        if not os.path.isfile(upload_file_path):
            raise Exception(f"文件{upload_file_path}不存在")
        else:
            try:
                self.client.upload_file(upload_file_path, bucketName, storage_path)
                DB.insert('file_common_table', 
                    {
                    'file_id': file_id,
                    'file_source': file_source,
                    'skill_description': skill_description,
                    'file_path': file_path,
                    'file_name': file_name,
                    'upload_user_id': user_id,
                    'upload_user_name': user_name
                    }
                )
            except Exception as e:
                raise Exception(f"COS上传失败: {e}")
            return file_id
    
    def download_file(self,file_id: str,local_path: str) -> bool:
        """
        从 COS 下载文件到本地

        Args:
            file_id (str): 文件ID
            local_path (str): 本地存储路径

        Returns:
            bool: 下载成功返回 True，失败返回 False

        Raises:
            Exception: 数据库连接失败、文件不存在或下载失败时抛出异常
        """
        if not DB.connect():
            raise Exception("数据库连接失败")
        
        try:
            col = DB.select('file_common_table', where={'file_id': file_id})
            DB.disconnect()
            storage_path = (col[0]['file_source'] + '/' + col[0]['skill_description'] + '/' + col[0]['file_path'] + '/' + col[0]['file_name'])
            self.client.download_file(bucketName, storage_path, local_path)
        except Exception as e:
            raise Exception(f"COS下载{storage_path}失败。 {e}")
        return True

    def generate_download_url(self,file_id: str) -> str:
        """
        生成文件的临时下载链接

        Args:
            file_id (str): 文件ID
        Returns:
            str: 生成的下载链接,有效期为30天

        Raises:
            Exception: 数据库连接失败或文件不存在时抛出异常
        """
        if not DB.connect():
            raise Exception("数据库连接失败")
        
        try:
            col = DB.select('file_common_table', where={'file_id': file_id})
            DB.disconnect()
            storage_path = (col[0]['file_source'] + '/' + col[0]['skill_description'] + '/' + col[0]['file_path'] + '/' + col[0]['file_name'])
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucketName, 'Key': storage_path},
                ExpiresIn=3600*24*30, HttpMethod='GET'  # 30天过期
            )
            return url
        except Exception as e:
            raise Exception(f"COS生成{storage_path}的下载链接失败。{e}")

    def upload_object(self, storage_path: str, upload_stream: BytesIO, user_id: str, user_name: str) -> str:
        """
        上传二进制流到 COS

        Args:
            storage_path (str): COS 存储路径,格式为“文件来源/技能描述/文件路径/文件名”
            upload_stream (BytesIO): 文件数据流
            user_id (str): 用户 ID
            user_name (str): 用户名

        Returns:
            str: 生成的文件ID

        Raises:
            Exception: 数据库连接失败或上传失败时抛出异常
        """
        if not DB.connect():
            raise Exception("数据库连接失败")
        
        storage_path_l = storage_path.replace("\\","/")
        storage_path_l = storage_path_l.split("/")
        file_source = storage_path_l[0]
        skill_description = storage_path_l[1]
        file_path = "/".join(storage_path_l[2:-1])
        file_name = storage_path_l[-1]
        file_id = file_id_generator()

        try:
            self.client.put_object(Body=upload_stream, Bucket=bucketName, Key=storage_path)
            DB.insert('file_common_table', 
                {
                'file_id': file_id,
                'file_source': file_source,
                'skill_description': skill_description,
                'file_path': file_path,
                'file_name': file_name,
                'upload_user_id': user_id,
                'upload_user_name': user_name
                }
            )
            DB.disconnect()
            return file_id
        except Exception as e:
            raise Exception(f"upload_object异常。 {e}")
        return file_id
    def get_object(self, file_id: str) -> bytes:
        """
        从 COS 获取文件的二进制流

        Args:
            file_id (str): 文件ID

        Returns:
            str: 文件的二进制流

        Raises:
            Exception: 数据库连接失败或获取失败时抛出异常
        """
        if not DB.connect():
            raise Exception("数据库连接失败")
        
        try:
            col = DB.select('file_common_table', where={'file_id': file_id})
            DB.disconnect()
            storage_path = (col[0]['file_source'] + '/' + col[0]['skill_description'] + '/' + col[0]['file_path'] + '/' + col[0]['file_name'])
            resp = self.client.get_object(Bucket=bucketName, Key=storage_path)
            ret = resp['Body'].read()
            return ret
        except Exception as e:
            raise Exception(f"get_object异常。{e}")
