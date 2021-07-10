#!./venv/bin/python
#
#  setup for this is:
#  sudo apt install python3-venv
#  python3 -m venv venv
#  venv/bin/pip3 install requests
#  venv/bin/pip3 install pyaml
#

import requests
import re
import yaml
import time
from http.server import HTTPServer, BaseHTTPRequestHandler


REL_ROOT=2
REL_STANDALONE=3
REL_CHILD=4

with open('config.yml') as f:
  config = yaml.safe_load(f)

hs_url = config['homeseer']['url']
if not hs_url.startswith('http'):
  hs_url = f'http://{hs_url}'
hs_user = config['homeseer']['user']
hs_pass = config['homeseer']['pass']

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        r = requests.get(f'{hs_url}/JSON?request=getstatus&excludeevents=true', auth=(hs_user, hs_pass))
        data = r.json()

        for item in data['Devices']:
          parent_name=''
          parent_ref=''
          if item['relationship'] == REL_CHILD:
            try:
              parent=list(filter(lambda e: e['ref'] == item['associated_devices'][0], data['Devices']))[0]
              parent_name = parent['name']
              parent_ref = parent['ref']
            except:
              parent_name = 'none'
          elif item['relationship'] == REL_ROOT:
            parent_name = 'root'
          elif item['relationship'] == REL_STANDALONE:
            parent_name = 'standalone'

          from_epoch = time.time_ns() // 1000000
          self.wfile.write(bytes(f'homeseer_device{{ref="{item["ref"]}", name="{item["name"]}", location="{item["location"]}", floor="{item["location2"]}", parent_name="{parent_name}", parent_ref="{parent_ref}"}} {item["value"]} {from_epoch}\n', 'utf-8'))

httpd = HTTPServer((config['server']['host'], config['server']['port']), SimpleHTTPRequestHandler)
httpd.serve_forever()
