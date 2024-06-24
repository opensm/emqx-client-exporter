import urllib.request
import json
import base64
import pandas as pd
import os, logging

loglevel = os.environ.get("LOGLEVEL")
if loglevel:
    loglevel = loglevel.upper()
    if not hasattr(logging, loglevel):
        loglevel_obj = getattr(logging, "INFO")
    else:
        loglevel_obj = getattr(logging, loglevel)
else:
    loglevel_obj = getattr(logging, "INFO")

logger = logging.getLogger(__name__)
logger.setLevel(level=loglevel_obj)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
logger.addHandler(console)


class EMQXObject:
    def __init__(self, data):
        self.data = data

    def __json__(self):
        pass


class PYMServer:
    url = None
    headers = dict()
    client = None

    def connect(self, host, port, username, password, api_version="v5"):
        """
        :param host:
        :param port:
        :param username:
        :param password:
        :param api_version:
        :return:
        """
        if port == 80:
            self.url = "http://{}/api/{}".format(host, api_version)
        elif port == 443:
            self.url = "https://{}/api/{}".format(host, api_version)
        else:
            self.url = "https://{}:{}/api/{}".format(host, port, api_version)
        auth_header = "Basic " + base64.b64encode((username + ":" + password).encode()).decode()
        self.headers['Content-Type'] = "application/json"
        self.headers['Authorization'] = auth_header

    def get_hu_clients(self):
        """
        :return: 获取客户端情况
        """
        self.client = urllib.request.Request(self.url + "/clients?conn_state=connected")
        for key, value in self.headers.items():
            self.client.add_header(key, value)
        data = self.run_query()
        df = pd.DataFrame(data)
        num_rows_containing_foo = df['clientid'].str.contains('HU').sum()
        return num_rows_containing_foo

    def get_tbox_clients(self):
        """
        :return:
        """
        self.client = urllib.request.Request(self.url + "/clients?conn_state=connected")
        for key, value in self.headers.items():
            self.client.add_header(key, value)
        data = self.run_query()
        df = pd.DataFrame(data)
        rows_without_string = ~df['clientid'].str.contains('HU')
        count_rows_without_string = rows_without_string.sum()
        return count_rows_without_string

    def run_query(self):
        """
        :return:
        """
        with urllib.request.urlopen(self.client) as response:
            data = json.loads(response.read().decode())
            return data['data']


if __name__ == '__main__':
    server = PYMServer()
    server.connect("uat-emqx.kayyi.com", 443, "42a760d3372cd36a", "Jb79BzVJ9B80KtBqJFkjF4JqO9AV2OTX5vgKWHj3epJ5vJ")
    print(server.get_hu_clients())
    print(server.get_tbox_clients())
