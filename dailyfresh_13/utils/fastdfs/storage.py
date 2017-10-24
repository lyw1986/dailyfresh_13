from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

class FastDFSStorage(Storage):
    def __init__(self, client_conf=None, fastdfs_url=None):
        if client_conf is None:
            client_conf = settings.FASTDFS_CLIENT_CONF

        self.client_conf = client_conf

        if fastdfs_url is None:
            fastdfs_url = settings.FASTDFS_URL

        self.fastdfs_url = fastdfs_url

    def _save(self, name, content):
        file_data = content.read()

        client = Fdfs_client(self.client_conf)

        try:
            ret = client.upload_by_buffer(file_data)

        except Exception as e:
            print(e)

            raise

        if ret.get('Status') == "Upload successed.":
            file_id = ret.get("Remote file_id")
            return file_id

        else:
            raise Exception('上传到FastDFS失败')

    def _open(self, name, mode='rb'):
        pass

    def exists(self, name):
        return False

    def url(self, name):
        return self.fastdfs_url + name

