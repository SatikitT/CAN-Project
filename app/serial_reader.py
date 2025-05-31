import serial

class SerialReader:
    def __init__(self, port, baudrate=1152000):
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def read_data(self):
        return self.ser.read_all()
