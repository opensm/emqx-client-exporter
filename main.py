# coding: utf8
import copy
import os
import time

from flask import Flask, Response
from gevent.pywsgi import WSGIServer
from prometheus_client import Summary, generate_latest
from prometheus_client.core import CollectorRegistry

from emqxlibs import EMQXItems

app = Flask(__name__)

LAST_METRICS_TIME = None

__METRICS__ = [
    'emqx_clients'
]

__LABELS__ = [
    "address",
    "client_type"
]


class Monitor:
    def __init__(self):
        #
        self.collector_registry = CollectorRegistry(auto_describe=False)
        self.emqx_clients = None
        labels = copy.deepcopy(__LABELS__)

        self.emqx_clients_summary = Summary(
            name="emqx_clients",
            documentation="统计emqx客户端连接数",
            labelnames=labels,
            registry=self.collector_registry
        )

    def billing_summary(self, summary_function, **kwargs):
        """
        :param summary_function:
        :param kwargs:
        :return:
        """
        summary_class = getattr(self, summary_function)
        self.emqx_clients = EMQXItems(**kwargs)

        data = list()
        hu_clients_counts = 0
        tbox_clients_counts = 0
        for x in self.emqx_clients:
            hu_clients_counts = hu_clients_counts + x[0]
            tbox_clients_counts = tbox_clients_counts + x[1]
        data.append({
            "address": kwargs['host'],
            "client_type": "tbox",
            "value": tbox_clients_counts
        })
        data.append({
            "address": kwargs['host'],
            "client_type": "hu",
            "value": hu_clients_counts
        })

        if not data:
            summary_class.labels(*__LABELS__).observe(0)
        else:
            #
            temp_labels = list()
            for x in data:
                value = x.pop('value')
                summary_class.labels(*x.values()).observe(float(value))
                temp_labels.append(x.values())


@app.route('/metrics/health')
def health():
    return Response("success", mimetype="text/plain")


@app.route('/metrics', methods=['GET'])
def metrics_billing():
    global LAST_METRICS_TIME
    host = os.environ.get("host", None)
    port = os.environ.get("port", None)
    username = os.environ.get("username", None)
    password = os.environ.get("password", None)
    m_monitor = Monitor()
    m_monitor.billing_summary(
        summary_function='emqx_clients_summary',
        host=host,
        port=port,
        username=username,
        password=password
    )
    LAST_METRICS_TIME = int(time.time())
    return Response(generate_latest(m_monitor.collector_registry), mimetype="text/plain")


if __name__ == '__main__':
    print("Server started: 0.0.0.0:8080")
    WSGIServer(('0.0.0.0', 8080), app).serve_forever()
