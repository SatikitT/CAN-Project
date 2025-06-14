import tkinter as tk
from tkinter import ttk, filedialog

from PIL import Image, ImageTk

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use("TkAgg")

import serial.tools.list_ports

import threading

from plotter import Plotter

READ_INTERVAL = 100

class LogicAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Logic Analyzer")
        self.geometry("1600x900")

        style = ttk.Style(self)
        style.configure('TCheckbutton', font = 11)

        self.configure(bg="white")

        self.stop_event   = threading.Event()
        self.serial_thr   = None
        
        self.after_id = None

        self.load_image()
        self.create_top_panel()
        self.create_plot_area()
        self.get_serial_ports()
        self.update_serial_ports()

        self.plotter = Plotter(self)
        self.plotter.ax = self.ax        

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_image(self):
        self.refresh_icon = ImageTk.PhotoImage(Image.open("app/icons/refresh.png").resize((36, 36)))
        self.start_icon   = ImageTk.PhotoImage(Image.open("app/icons/start.png").resize((24, 24)))
        self.stop_icon    = ImageTk.PhotoImage(Image.open("app/icons/pause.png").resize((24, 24)))
        self.reset_icon   = ImageTk.PhotoImage(Image.open("app/icons/record.png").resize((24, 24)))

    def create_top_panel(self):
        top_frame = tk.Frame(self, bg="lightblue", height=100)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)

        # Port
        tk.Label(top_frame, text="Port", bg=top_frame['bg'], font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))
        self.port_combo = ttk.Combobox(top_frame, values=[], width=20)
        self.port_combo.pack(side=tk.LEFT)

        tk.Button(top_frame, image=self.refresh_icon, bg=top_frame['bg'], bd=0, command=self.update_serial_ports).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, image=self.start_icon, bg=top_frame['bg'], bd=0, command=self.start).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, image=self.stop_icon, bg=top_frame['bg'], bd=0, command=self.stop).pack(side=tk.LEFT, padx=10)

        tk.Label(top_frame, text="Display:", bg=top_frame['bg'], font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))

        self.bit_chkbox = tk.BooleanVar(value=True)
        self.hex_chkbox = tk.BooleanVar(value=True)
        self.hili_chkbox = tk.BooleanVar(value=True)
        self.text_chkbox = tk.BooleanVar(value=True)
        self.frametype_chkbox = tk.BooleanVar(value=True)

        cb_bit = tk.Checkbutton(top_frame, text="bits", bg=top_frame['bg'], font=("Segoe UI", 20), variable=self.bit_chkbox, command=self.refresh_plot)
        cb_bit.pack(side=tk.LEFT, padx=(20, 5))

        cb_hex = tk.Checkbutton(top_frame, text="hex", bg=top_frame['bg'], font=("Segoe UI", 20), variable=self.hex_chkbox, command=self.refresh_plot)
        cb_hex.pack(side=tk.LEFT, padx=(20, 5))

        cb_hili = tk.Checkbutton(top_frame, text="highlight", bg=top_frame['bg'], font=("Segoe UI", 20), variable=self.hili_chkbox, command=self.refresh_plot)
        cb_hili.pack(side=tk.LEFT, padx=(20, 5))

        cb_stuff = tk.Checkbutton(top_frame, text="Stuff", bg=top_frame['bg'], font=("Segoe UI", 20), variable=self.text_chkbox, command=self.refresh_plot)
        cb_stuff.pack(side=tk.LEFT, padx=(20, 5))

        cb_frametype = tk.Checkbutton(top_frame, text="Frame type", bg=top_frame['bg'], font=("Segoe UI", 20), variable=self.frametype_chkbox, command=self.refresh_plot)
        cb_frametype.pack(side=tk.LEFT, padx=(20, 5))

        self.all_checkbuttons = [cb_bit, cb_hex, cb_hili, cb_stuff, cb_frametype]

        # Save Raw Button
        tk.Button(top_frame, text="Save Raw", bg="lightgrey", font=("Segoe UI", 14), command=self.save_raw_data).pack(side=tk.LEFT, padx=10)

        # Save Graph Button
        tk.Button(top_frame, text="Save Graph", bg="lightgrey", font=("Segoe UI", 14), command=self.save_graph_image).pack(side=tk.LEFT, padx=10)

    def create_plot_area(self):
        self.figure, self.ax = plt.subplots(figsize=(10, 5))
        self.ax.set_xlabel("Time (ticks)\n 0.1 us/tick")
        self.ax.set_ylabel("Logic level")
        self.ax.set_xlim(0, 2500)
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def update_serial_ports(self):
        available_ports = self.get_serial_ports()
        self.port_combo['values'] = available_ports
        if available_ports:
            self.port_combo.set(available_ports[0])
        else:
            self.port_combo.set("No Ports")

    def start(self):
        
        self.stop_event.clear()
        
        # check if port selected
        selected_port = self.port_combo.get()
        if "No Ports" in selected_port or not selected_port:
            print("No valid port selected.")
            return

        try:
            
            if self.plotter.reader and self.plotter.reader.ser:
                if self.plotter.reader.ser.is_open and self.plotter.reader.ser.port == selected_port:
                    print(f"Already connected to {selected_port}")
                    return

            self.serial_thr = threading.Thread(
                target=self.plotter.start,
                args=(selected_port,),
                kwargs={'baudrate': 1152000},
                daemon=True
            )

            self.serial_thr.start()

            # self.anim = FuncAnimation(self.figure, self.plotter.update, interval=100, blit=False)

            self.after(READ_INTERVAL, self.periodic_update)
            self.canvas.get_tk_widget().update_idletasks()

            print(f"Started on {selected_port}")
        except Exception as e:
            print(f"Error opening port: {e}")
    
    def periodic_update(self):
        try:
            self.plotter.update(None)
            self.canvas.draw()
        except Exception as e:

            print(f"\nException caught: {e}\n")
            self.plotter.decoder.reset_data()
            return         

        if not self.stop_event.is_set():
            self.after_id = self.after(READ_INTERVAL, self.periodic_update)

    def stop(self):
        self.stop_event.set()
        self.plotter.reader.disconnect()
        
        # Cancel the after loop
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        print("Stop clicked")

    def reset(self):
        print("Reset clicked")

    def on_close(self):
        self.quit()
        self.destroy()

    def save_raw_data(self):
        raw_data_list = self.plotter.raw_data_log
        if not raw_data_list:
            print("No raw data to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt")],
                                                title="Save Raw Data")
        if file_path:
            with open(file_path, "w") as file:
                for raw in raw_data_list:
                    file.write(repr(raw) + '\n')  # เขียนเป็น b'...' format
            print(f"Raw data saved to {file_path}")

    def save_graph_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG Image", "*.png")],
                                                 title="Save Graph Image")
        if file_path:
            self.figure.savefig(file_path)
            print(f"Graph image saved to {file_path}")
    
    def disable_all_checkboxes(self):
        for cb in self.all_checkbuttons:
            cb.config(state='disabled')

        self.bit_chkbox.set(False)
        self.hex_chkbox.set(False)
        self.hili_chkbox.set(False)
        self.text_chkbox.set(False)
        self.frametype_chkbox.set(False)

    def enable_all_checkboxes(self):
        self.bit_chkbox.set(True)
        self.hex_chkbox.set(True)
        self.hili_chkbox.set(True)
        self.text_chkbox.set(True)
        self.frametype_chkbox.set(True)

        for cb in self.all_checkbuttons:
            cb.config(state='normal')
    
    def refresh_plot(self):
        try:
            self.plotter.setup_graph(self.plotter.decoder.bit_data)
            bits, stuff_pos = self.plotter.decoder.remove_stuff_bits(self.plotter.decoder.bit_data)
            frames = self.plotter.decoder.decode_frame_type(bits)
            self.plotter.draw_frame(self.plotter.decoder.bit_data, frames, stuff_pos)
            self.canvas.draw()
        except Exception as e:
            print(f"Error refreshing plot: {e}")

if __name__ == "__main__":
    app = LogicAnalyzerApp()
    app.mainloop()

