#!/usr/bin/env python3
import json
import subprocess
import sys
import uuid
from xml.etree import ElementTree as ETree

try:
    file_path = sys.argv[1]
except IndexError:
    file_path = None
    print('WARN: No output dir provided. Report will not be saved.')

try:
    process = subprocess.Popen(
        ['lshw', '-xml'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = process.communicate()
except FileNotFoundError:
    print('Required utility not found. Install lshw package and try again.')
    sys.exit(1)

system_data = {}
tree = ETree.fromstring(out)
gateway = tree.findall('node')
try:
    system_data['manufacturer'] = gateway[0].find('vendor').text
except AttributeError:
    system_data['manufacturer'] = 'Unknown'
try:
    system_data['product_name'] = gateway[0].find('product').text
except AttributeError:
    system_data['product_name'] = 'Unknown'

try:
    system_data['serial_number'] = gateway[0].find('serial').text
except AttributeError:
    system_data['serial_number'] = 'Unknown'

try:
    settings = gateway[0].find('configuration').findall('setting')
except AttributeError:
    settings = None
uuid_elem = None
if settings:
    for element in settings:
        if element.attrib.get('id') == 'uuid':
            uuid_elem = element

if uuid_elem:
    system_data['uuid'] = uuid_elem.attrib.get('uuid')
else:
    system_data['uuid'] = None

motherboard = gateway[0].findall('node')[0]
if motherboard is not None:
    try:
        system_data['motherboard_name'] = motherboard.find('product').text
    except AttributeError:
        system_data['motherboard_name'] = 'unknown'
    devices = motherboard.findall('node')

if not motherboard:
    devices = []

memory = None
cpu = None  # For further development
for device in devices:
    if 'memory' in device.attrib.get('id'):
        memory = device
    if 'cpu' in device.attrib.get('id'):
        cpu = device

if not memory:
    print('Could not get memory information. Dying.')
    sys.exit(1)

system_data['mem_available'] = memory.find('size').text
system_data['num_banks'] = len(memory.findall('node'))
system_data['banks'] = []

for bank in memory.findall('node'):
    dct = {
        'id': bank.attrib.get('id'),
        'size': bank.find('size').text
    }
    system_data['banks'].append(dct)
file_name = system_data['serial_number']
if not file_name:
    file_name = str(uuid.uuid4())
if file_path:
    with open(file_path.rstrip("/") + f"/{file_name}.json",
              'w') as f:
        f.write(json.dumps(system_data, indent=4))

else:
    print(
        json.dumps(system_data, indent=4)
    )
