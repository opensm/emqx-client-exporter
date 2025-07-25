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
    _client = None

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
            self.url = "http://{}:{}/api/{}".format(host, port, api_version)
        auth_header = "Basic " + base64.b64encode((username + ":" + password).encode()).decode()
        self.headers['Content-Type'] = "application/json"
        self.headers['Authorization'] = auth_header

    def clients(self, conn_state="connected", _page=1, _limit=100):
        """
        :param conn_state:
        :param _page:
        :param _limit:
        :return:
        """

        data = self.run_query(
            uri="clients",
            params="conn_state={}&page={}&limit={}".format(
                conn_state,
                _page,
                _limit
            ))
        if not data:
            return None
        df = pd.DataFrame(data)
        hu_client_counts = df['clientid'].str.contains('-HU', case=False, na=False).sum()
        tbox_client_counts = (~df['clientid'].str.contains('-HU', case=False, na=False)).sum()
        return hu_client_counts, tbox_client_counts

    def run_query(self, uri, params=None):
        """
        :param uri:
        :param params:
        :return:
        """
        if params is not None:
            _url = self.url + "/{}?{}".format(uri, params)
            # self._client = urllib.request.Request(self.url + "/{}?{}".format(uri, params))
        else:
            _url = self.url + "/{}".format(uri)
        logger.info(_url)
        self._client = urllib.request.Request(_url)
        for key, value in self.headers.items():
            self._client.add_header(key, value)
        with urllib.request.urlopen(self._client) as response:
            data = json.loads(response.read().decode())
            return data['data']


class EMQXItems:
    _offset = 1

    def __init__(self, **kwargs):
        self.emqx_client = PYMServer()
        self.emqx_client.connect(**kwargs)

    def __next__(self):
        data = self.emqx_client.clients(_page=self._offset, _limit=500)
        self._offset = self._offset + 1
        if not data:
            raise StopIteration
        return data

    def __iter__(self):
        return self


__all__ = ["EMQXItems"]
