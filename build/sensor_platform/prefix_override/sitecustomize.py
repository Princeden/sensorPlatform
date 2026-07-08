import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/phom/Projects/sensorPlatform/install/sensor_platform'
