from decoder import CANDecoder
from serial_reader import SerialReader
import numpy as np
import time

class Plotter:

    def __init__(self, app):

        self.decoder = CANDecoder()
        self.reader = None
        self.ax = None
        self.app = app

        self.font_size = 10
        self.font_color = 'black'
        self.raw_data_log = []

        self.plot_timestamp = []

        self.frame_color = {"IDLE":"#45c0de", 
                            "IDLE ":"#45c0de",
                            "SOF":"#b1b6ba",
                            "ID":"#92c255",
                            "RTR":"#49b45d",
                            "r0":"#49b45d",
                            "r1":"#49b45d",
                            "SRR":"#49b45d",
                            "IDE":"#49b45d",
                            "BASE ID":"#92c255",
                            "EXT ID":"#92c255",
                            "DLC":"#00a765",
                            "Data":"#028fc3",
                            "CRC":"#b70032",
                            "CD":"#b70032",
                            "ACK":"#fbb900",
                            "AD":"#fbb900",
                            "EOF":"#ef7c00",
                            "IFS":"#757575"}

    def start(self, port, baudrate):
        self.reader = SerialReader(port, baudrate)

    def bits_to_hex(self, bits):
        if bits:
            return hex(int(bits, 2))
        else:
            return '0x0' 
    
    def retrive_bit_timestamp(self, timestamp_data):
        actual_bit_timestamp = []
        for time_index in range(0, len(timestamp_data)-1,2):
            t1 = timestamp_data[time_index]
            t2 = timestamp_data[time_index + 1] 
            time_diff = t2 - t1
            bit_count = 0

            while time_diff > 20:
                bit_count += 1
                time_diff -= 20
            if time_diff > 8:
                bit_count += 1

            for i in np.arange(t1, t2, (t2 - t1) / bit_count):
                actual_bit_timestamp.append(i)
                actual_bit_timestamp.append(i + (t2 - t1) / bit_count)

        actual_bit_timestamp[0] = 0

        return actual_bit_timestamp

    def setup_graph(self, data):

        self.ax.clear()
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.set_xlabel('Time (ticks)')
        self.ax.set_ylabel('Logic Level')
        self.ax.grid(True, axis='y')

        plotting_lim = (len(data) * 20) + 500

        self.ax.set_xlim(0, plotting_lim)
        
        self.plot_timestamp = self.retrive_bit_timestamp(self.decoder.timestamp_data)

        print(self.plot_timestamp)
        # # draw dot line
        # for i in range(0, plotting_lim, 20):
        #     self.ax.axvline(i, color='gray', linestyle='--', linewidth=0.5)

    def get_pos(self, bit_cnt, offset_bits=4):
        pos = 0
        act_bit_mins_4 = bit_cnt - offset_bits
        if bit_cnt > 3 and (bit_cnt - offset_bits) * 2 < len(self.plot_timestamp):
            time_diff = self.plot_timestamp[act_bit_mins_4 * 2 + 1] - self.plot_timestamp[act_bit_mins_4 * 2]
            pos = self.plot_timestamp[act_bit_mins_4 * 2] + time_diff / 2 + 80
        elif (bit_cnt - offset_bits) * 2 >= len(self.plot_timestamp):
            cnt_from_last = bit_cnt - len(self.plot_timestamp) // 2
            pos = self.plot_timestamp[-1] + cnt_from_last * 20 + 10
        else:
            pos = bit_cnt * 20 + 10 
        
        return pos

    def draw_frame(self, bit_data, frames, stuff_bit_pos):

        actual_bit_cnt = 0
        offset_bits = 4

        for frame_info in frames:
            
            x_pos = self.get_pos(actual_bit_cnt, offset_bits) 

            frame_type_label = f"Frame type: {frame_info['FrameType']} {frame_info['FrameSubtype']} Frame"
            self.ax.text(x_pos, 1.05, frame_type_label,
                        fontsize=12, fontweight='bold', verticalalignment='bottom',
                        horizontalalignment='left', color='black',
                        bbox=dict(facecolor='yellow', edgecolor='black', boxstyle='round,pad=0.13'))
            
            if actual_bit_cnt == 0:
                frame_info = {'IDLE': [1] * offset_bits, **frame_info}

            for part, bits in frame_info.items():
                
                if part in ('FrameType', 'FrameSubtype'):
                    continue

                if type(bits) == int:
                    bits = [bits]

                x_pos = self.get_pos(actual_bit_cnt, offset_bits) 

                if self.app.bit_chkbox.get():
                    # draw part name
                    self.ax.text(
                        x_pos, -0.46, part,
                        fontsize=self.font_size,
                        ha='center', va='baseline',
                        color='black',
                        rotation=90,
                        bbox=dict(facecolor='yellow', edgecolor='black', boxstyle='round,pad=0.13')
                    )
                bit_text = ''.join(str(b) for b in bits)
                bit_decoded = self.bits_to_hex(bit_text)
                
                if self.app.hex_chkbox.get():
                    # draw hex data of each part
                    self.ax.text(
                        x_pos, -0.23, bit_decoded,
                        fontsize=self.font_size,
                        ha='center', va='baseline',
                        color='black',
                        rotation=90,
                        bbox=dict(facecolor='yellow', edgecolor='black', boxstyle='round,pad=0.13')
                    )
                
                for bit in bits:

                    if actual_bit_cnt - offset_bits in stuff_bit_pos:
                        x_pos = self.get_pos(actual_bit_cnt, offset_bits) 
                        
                        if self.app.text_chkbox.get():
                            # draw stuff text
                            self.ax.text(
                                x_pos, -0.46, 'stuff',
                                fontsize=self.font_size,
                                fontweight='bold',
                                ha='center', va='baseline',
                                color='white',
                                rotation=90,
                                bbox=dict(facecolor='red', edgecolor='black', boxstyle='round,pad=0.12')
                            )
                        
                        if self.app.bit_chkbox.get():
                            # draw stuff bit 
                            self.ax.text(x_pos,  -0.33, bit_data[actual_bit_cnt - offset_bits], fontsize=self.font_size, ha='center', va='center', color=self.font_color)
                        
                        if self.app.hili_chkbox.get():
                            act_bit_mins_4 = actual_bit_cnt - offset_bits
                            t1 = self.plot_timestamp[act_bit_mins_4 * 2] + 80
                            t2 = self.plot_timestamp[act_bit_mins_4 * 2 + 1] + 80
                            self.ax.axvspan(t1, t2, facecolor='#ff6961', alpha=0.5)
                            self.ax.axvline(t2, color='grey', linestyle='-', linewidth=0.5)
                        actual_bit_cnt += 1
                    
                    x_pos = self.get_pos(actual_bit_cnt, offset_bits)

                    if self.app.bit_chkbox.get():
                        # draw bit 
                        self.ax.text(x_pos,  -0.33, str(bit), fontsize=self.font_size, ha='center', va='center', color=self.font_color)
                    
                    if part in self.frame_color.keys() and self.app.hili_chkbox.get():
                        # draw colored plane
                        act_bit_mins_4 = actual_bit_cnt - offset_bits
                        if actual_bit_cnt > 3 and act_bit_mins_4 * 2 < len(self.plot_timestamp):
                            t1 = self.plot_timestamp[act_bit_mins_4 * 2] + 80
                            t2 = self.plot_timestamp[act_bit_mins_4 * 2 + 1] + 80
                            self.ax.axvspan(t1, t2, facecolor=self.frame_color[part], alpha=0.5)
                            self.ax.axvline(t2, color='grey', linestyle='-', linewidth=0.5)
                        else:
                            self.ax.axvspan(x_pos - 10, x_pos + 10, facecolor=self.frame_color[part], alpha=0.5)
                            self.ax.axvline(x_pos + 10, color='grey', linestyle='-', linewidth=0.5)

                    actual_bit_cnt += 1

        x, y = self.decoder.get_plot_data()

        idle_duration = 20
        start_offset = offset_bits * idle_duration
        x = [1, 1] + x
        y = [0, start_offset] + [yi + start_offset for yi in y]

        # ต่อท้ายค่าจุดสุดท้ายด้วย logic level เดิม และเวลาเพิ่มอีกช่วงเพื่อให้ถึง IFS
        if len(x) > 0 and len(y) > 0:
            x.append(x[-1])  # logic level คงเดิม
            y.append(y[-1] + idle_duration * 8)  # เพิ่มเวลาอีก ~160 ticks เพื่อลากถึง IFS

        self.ax.step(y, x, where='post', color='blue', linewidth=2)

    def update(self, frame):
        data = self.reader.read_data()

        if data:
            self.raw_data_log.append(data)
            print(data)
            self.decoder.decode_8byte_data(data)
            print(self.decoder.bit_data)

            if not self.decoder.bit_data:
                return
            
            self.setup_graph(self.decoder.bit_data)
            bits, stuff_pos = self.decoder.remove_stuff_bits(self.decoder.bit_data)
            frames = self.decoder.decode_frame_type(bits)
            self.draw_frame(self.decoder.bit_data, frames, stuff_pos)
                    