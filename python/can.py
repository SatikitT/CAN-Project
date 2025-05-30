from matplotlib.animation import FuncAnimation
import serial
import struct
import matplotlib.pyplot as plt

class CANPlotter:

    def __init__(self):

        self.state_data = []
        self.timestamp_data = []
        self.bit_data = []
        self.current_bits = []

        self.offset = 8
        self.total_time = 0
        self.last_time = 0
        self.bit_duration = 20 

        self.ser = None
        self.ax = None

    def start(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def reset_data(self):
        self.state_data.clear()
        self.timestamp_data.clear()
        self.bit_data.clear()
        self.total_time = 0
        self.last_time = 0
        
    def decode_8byte_aligned(self, data):
        i = 0

        while i < len(data):

            if data[i:i+3] == b'\x11\x00\x01' or data[i:i+3] == b'\x11\x01\x01':
                record = data[i:i+8]
                if len(record) < 8:
                    continue

                state = record[1]
                if len(self.state_data) > 1 and state == self.state_data[-1]:
                    i += 8
                    continue

                timestamp = struct.unpack("<I", record[4:8])[0] 
            
                #Debugging output
                #print(f"{current_bit_index} Rec: {record[0:4]}          {record[4:8]}           Lev: {state}    Dur: {timestamp}")
                
                if len(self.timestamp_data) > 0 and timestamp < self.timestamp_data[-1]:
                    self.reset_data()

                if len(self.state_data) >= 1:
                    self.state_data.append(self.state_data[-1])
                    self.timestamp_data.append(timestamp)
                    
                self.state_data.append(state)
                self.timestamp_data.append(timestamp)

                duration = timestamp - self.last_time

                while duration > self.offset:
                    self.bit_data.append(1 - state)
                    duration -= self.bit_duration
                    pass

                self.last_time = timestamp
                
                i += 8
            else:
                i += 1

    def bits_to_hex(self, bits):
        if bits:
            return hex(int(bits, 2))
        else:
            return '0x0' 


    def update(self, frame):
        print("Running")
        
        data = self.ser.read_all()
        if data:
            print(data)
            self.ax.clear()
            
            frame_labels = {
                0: "SOF",
                1: "ID",
                12: "RTR",
                13: "IDE",
                14: "r0",
                15: "DLC",
                19: "DATA0",
                27: "DATA1",
                35: "DATA2",
                43: "DATA3",
                51: "DATA4",
                59: "DATA5",
                67: "DATA6",
                75: "DATA7",
                83: "CRC",
                98: "DEL",
                99: "ACK",
                100: "DEL",
                101: "EOF",
                108: "IFS"
            }

            stuff_bit_count = 0
            count = 0
            last_bit = -1
            actual_idx = 0
            plotting_lim = 0

            print(len(self.bit_data))
            if len(self.bit_data) < 125:
                plotting_lim = 2500
            else:
                plotting_lim = (len(self.bit_data) * 20) + 250

            self.ax.set_ylim(-0.5, 1.5)
            self.ax.set_xlim(0, plotting_lim)
            self.ax.set_xlabel('Time (ticks)')
            self.ax.set_ylabel('Logic Level')
            self.ax.set_title('Live CAN Frame')
            self.ax.grid(True)

            self.decode_8byte_aligned(data)

            for i in range(0, plotting_lim, 20):
                self.ax.axvline(i, color='gray', linestyle='--', linewidth=0.5)

            for idx, bit in enumerate(self.bit_data):
                x_pos = idx * 20 + 10
                y_pos = 1.1
                self.ax.text(x_pos, y_pos, str(bit), fontsize=9, ha='center', va='center', color='blue')
                self.ax.text(x_pos, y_pos + 0.1, str(idx), fontsize=9, ha='center', va='center', color='blue', rotation=90)
            
                if bit == last_bit:
                    count += 1
                else:
                    if count >= 5:
                        stuff_bit_count += 1

                        self.ax.text(x_pos, 1.3, "stuff", fontsize=8, ha='center', va='center', color='red', rotation=90)
                        self.ax.axvspan(x_pos - 10, x_pos + 10, facecolor='red', alpha=0.1)
                        count = 0
                        last_bit = bit
                        continue
                    count = 1

                if actual_idx in frame_labels:
                    label = frame_labels[actual_idx]
                    
                    
                    x = idx * 20      
                    self.ax.axvline(x, color='black', linestyle='-', linewidth=1)
                    self.ax.text(x + 12, -0.3, label, rotation=90, fontsize=10, ha='center', va='bottom', color='black')
                    
                    if self.current_bits != '':
                        self.ax.text(x + 12, -0.4, self.bits_to_hex(''.join(str(b) for b in self.current_bits)), rotation=90, fontsize=10, ha='center', va='bottom', color='black')
                    
                    self.current_bits.clear()

                    if label in("EOF","IFS"):
                        count = 0
                    
                    if label == "IFS":
                        actual_idx = -3

                    if label == "CRC":
                        if len(self.bit_data) - idx <= 30:
                            self.bit_data.extend([1]*14)
                            self.state_data.append(1)
                            self.timestamp_data.append(self.timestamp_data[-1] + 14 * 20)

                last_bit = bit
                self.current_bits.append(bit)
                actual_idx += 1

            x = self.timestamp_data
            y = self.state_data

            if len(x) != 0:
                self.ax.step(x, y, where='post', color='blue', linewidth=1.5)
