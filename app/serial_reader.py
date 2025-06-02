import serial

class SerialReader:
    def __init__(self, port, baudrate=1152000):
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def read_data(self, non_blocking=False):
        if self.ser and self.ser.is_open:
            if non_blocking:
                return self.ser.read_all()  # non-blocking
            else:
                return self.ser.read(1024)  # potentially blocking
        return b''

    def disconnect(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("Serial port disconnected.")
            except Exception as e:
                print(f"Error closing port: {e}")
