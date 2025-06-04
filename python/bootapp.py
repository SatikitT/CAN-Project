import os 
import struct
import serial

MESSAGE_TOKEN               = 0x23
CHANGE_BANK_REQUEST         = 0x43
BOOT_UPDATE_REQUEST         = 0x42
FIRMWARE_VERSION_REQUEST    = 0x41

BOOT_ACK                    = 0x5f
BOOT_NACK                   = 0xaa    

def compute_crc(buff, length):
    crc = 0xFFFFFFFF

    for byte in buff[:length]:
        crc ^= byte
        for _ in range(32):
            if (crc & 0x80000000) == 1:
                crc = (crc >> 1) ^ 0x04C11DB7
            else:
                crc >>= 1

    return crc & 0xFFFFFFFF

def update_flash_mem(serial_com, file_name):
    WINDOW_SIZE = 128
    try:
        flash_bin_file = open(file_name, 'rb')
    except:
        Exception("Error opening file: {}".format(file_name))
    size = os.path.getsize(file_name)

    data_token = [MESSAGE_TOKEN, BOOT_UPDATE_REQUEST]
    data_token_bytes = bytes()
    data_token_bytes = data_token_bytes.join((struct.pack('<' + format, val) for format, val in zip('BB', data_token)))
    size_copy = size
    while size > 0:

        data_sent = flash_bin_file.read(WINDOW_SIZE)
        size = size - len(data_sent)
        data_sent = data_token_bytes + struct.pack('<H', len(data_sent)) + data_sent
        send_data_serial(serial_com, data_sent)
        print("Firmware updating")
        if read_boot_reply(serial_com) != BOOT_ACK:
            print("flash update failed")
            Exception("flash update failed")
            break

    if size == 0:
        print("Firmware update size = 0")
        print("Firmware update is over")


def read_boot_reply(serial_com):
    ack_value = serial_com.read(1)
    if len(ack_value) > 0 and ack_value[0] == BOOT_ACK:
        return BOOT_ACK
    else:
        print("Boot reply not received")
        return BOOT_NACK

def send_data_serial(serial_com, data):
    data = data + struct.pack('<I', compute_crc(data, len(data)))
    serial_com.write(data)

def read_firmware_version(serial_com):
    command_message = [MESSAGE_TOKEN, FIRMWARE_VERSION_REQUEST, 0]
    b = bytes()
    b = b.join((struct.pack('<' + format, val) for format, val in zip('BBH', command_message)))
    send_data_serial(serial_com, b)

    raw_data = serial_com.read(27)
    message = struct.unpack("%ds" % len(raw_data), raw_data)
    message = message[0].decode('utf-8')
    print(message)

def change_firmware(serial_com):
    command_message = [MESSAGE_TOKEN, CHANGE_BANK_REQUEST, 0]
    b = bytes()
    b = b.join((struct.pack('<' + format, val) for format, val in zip('BBH', command_message)))
    send_data_serial(serial_com, b)

    ack_value = read_boot_reply(serial_com)
    if ack_value == BOOT_ACK:
        print("Firmware changed successfully")
    else:
        print("Firmware change failed")

comport = "COM6"
serial_com = serial.Serial(comport, baudrate=115200, timeout=15)

message = "Hello from bootapp.py"

while True:
    command = input("Enter command (version, change, update, exit): ").strip().lower()
    if command == "version":
        read_firmware_version(serial_com)
    elif command == "change":
        change_firmware(serial_com)
    elif command == "update":
        file_name = "Bootloader.bin"  # Replace with your actual file name
        update_flash_mem(serial_com, file_name)
    elif command == "exit":
        print("Exiting bootapp.py")
        break
    else:
        print("Unknown command. Please try again.")
