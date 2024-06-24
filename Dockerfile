FROM python:3.10
WORKDIR /app
ADD requirements.txt /app/
RUN pip3 install -r  requirements.txt -i http://mirrors.aliyun.com/pypi/simple  --trusted-host mirrors.aliyun.com && rm /app/requirements.txt -f
ADD main.py emqxlibs.py /app
CMD ["python3", "main.py"]