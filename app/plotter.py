from decoder import CANDecoder
from serial_reader import SerialReader
import time

class Plotter:

    def __init__(self, app):

        self.decoder = CANDecoder()
        self.reader = None
        self.ax = None
        self.app = app

        self.font_size = 10
        self.font_color = 'black'

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
                            "CRC_DEL":"#b70032",
                            "ACK":"#fbb900",
                            "ACK_DEL":"#fbb900",
                            "EOF":"#ef7c00",
                            "IFS":"#dadee1"}

    def start(self, port, baudrate):
        self.reader = SerialReader(port, baudrate)

    def bits_to_hex(self, bits):
        if bits:
            return hex(int(bits, 2))
        else:
            return '0x0' 
    
    def setup_graph(self, data):

        self.ax.clear()
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.set_xlabel('Time (ticks)')
        self.ax.set_ylabel('Logic Level')
        self.ax.grid(True)

        plotting_lim = (len(data) * 20) + 500

        self.ax.set_xlim(0, plotting_lim)

        # draw dot line
        for i in range(0, plotting_lim, 20):
            self.ax.axvline(i, color='gray', linestyle='--', linewidth=0.5)

    def draw_frame(self, bit_data, frames, stuff_bit_pos):

        actual_bit_cnt = 0
        offset_bits = 4

        for frame_info in frames:

            frame_type_label = f"Frame type: {frame_info['FrameType']} {frame_info['FrameSubtype']} Frame"
            self.ax.text(0, 1.02, frame_type_label, transform=self.ax.transAxes,
                        fontsize=12, fontweight='bold', verticalalignment='bottom',
                        horizontalalignment='left', color='green')

            if actual_bit_cnt == 0:
                frame_info = {'IDLE': [1] * offset_bits, **frame_info}

            for part, bits in frame_info.items():
                
                if part in ('FrameType', 'FrameSubtype'):
                    continue

                if type(bits) == int:
                    bits = [bits]

                x_pos = actual_bit_cnt * 20 + 10

                if self.app.bit_chkbox.get():
                    # draw part name
                    self.ax.text(x_pos,  -0.49, part, fontsize=self.font_size, ha='center', va='baseline', color=self.font_color, rotation=90)

                bit_text = ''.join(str(b) for b in bits)
                bit_decoded = self.bits_to_hex(bit_text)
                
                if self.app.hex_chkbox.get():
                    # draw hex data of each part
                    self.ax.text(x_pos,  -0.3, bit_decoded, fontsize=self.font_size, ha='center', va='baseline', color=self.font_color, rotation=90)
                
                for bit in bits:

                    if actual_bit_cnt - offset_bits in stuff_bit_pos:
                        x_pos = actual_bit_cnt * 20 + 10
                        
                        if self.app.text_chkbox.get():
                            # draw stuff text
                            self.ax.text(x_pos,  -0.49, 'stuff', fontsize=self.font_size, ha='center', va='baseline', color=self.font_color, rotation=90)
                        
                        if self.app.bit_chkbox.get():
                            # draw stuff bit 
                            self.ax.text(x_pos,  -0.37, bit_data[actual_bit_cnt - offset_bits], fontsize=self.font_size, ha='center', va='center', color=self.font_color)
                        
                        if self.app.hili_chkbox.get():
                            # draw red plane
                            self.ax.axvspan(x_pos - 10, x_pos + 10, facecolor='#ff6961', alpha=0.5)
                        actual_bit_cnt += 1
                    
                    x_pos = actual_bit_cnt * 20 + 10

                    if self.app.bit_chkbox.get():
                        # draw bit 
                        self.ax.text(x_pos,  -0.37, str(bit), fontsize=self.font_size, ha='center', va='center', color=self.font_color)
                    
                    if part in self.frame_color.keys() and self.app.hili_chkbox.get():
                        # draw colored plane
                        self.ax.axvspan(x_pos - 10, x_pos + 10, facecolor=self.frame_color[part], alpha=0.5)

                    actual_bit_cnt += 1

        x, y = self.decoder.get_plot_data()

        idle_duration = 20
        y = [0, offset_bits * idle_duration] + [yi + offset_bits * idle_duration for yi in y]
        x = [1,1] + x

        self.ax.step(y, x, where='post', color='blue', linewidth=1.5)

    def update(self, frame):
        data = self.reader.read_data()
        if data:
            self.decoder.decode_8byte_data(data)
            self.setup_graph(self.decoder.bit_data)
            bits, stuff_pos = self.decoder.remove_stuff_bits(self.decoder.bit_data)
            frames = self.decoder.decode_frame_type(bits)
            self.draw_frame(self.decoder.bit_data, frames, stuff_pos)

            for b in range(len(self.decoder.bit_data)):
                x_pos = (b+4) * 20 + 10
                self.ax.text(x_pos,  -0.39, str(self.decoder.bit_data[b]), fontsize=self.font_size, ha='center', va='center', color=self.font_color)
                    
