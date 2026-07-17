import pyzed.sl as sl
def get_zed_serials():
    devices = sl.Camera.get_device_list()
    serials = []
    for dev in devices:
        serials.append(dev.serial_number)
print(get_zed_serials())
