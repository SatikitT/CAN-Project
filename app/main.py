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

        # self.state('zoomed')
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
        top_frame = tk.Frame(self, bg="lightgrey", height=100)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)

        # Port
        tk.Label(top_frame, text="Port", bg="lightgrey", font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))
        self.port_combo = ttk.Combobox(top_frame, values=[], width=20)
        self.port_combo.pack(side=tk.LEFT)

        tk.Button(top_frame, image=self.refresh_icon, bg="lightgrey", bd=0, command=self.update_serial_ports).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, image=self.start_icon, bg="lightgrey", bd=0, command=self.start).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, image=self.stop_icon, bg="lightgrey", bd=0, command=self.stop).pack(side=tk.LEFT, padx=10)
        # tk.Button(top_frame, image=self.reset_icon, bg="lightgrey", bd=0, command=self.reset).pack(side=tk.LEFT, padx=10)

        tk.Label(top_frame, text="Display:", bg="lightgrey", font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))

        self.bit_chkbox = tk.BooleanVar(value=True)
        self.hex_chkbox = tk.BooleanVar(value=True)
        self.hili_chkbox = tk.BooleanVar(value=True)
        self.text_chkbox = tk.BooleanVar(value=True)

        tk.Checkbutton(top_frame, text="bits", bg="lightgrey", font=("Segoe UI", 20), variable=self.bit_chkbox).pack(side=tk.LEFT, padx=(20, 5))
        tk.Checkbutton(top_frame, text="hex", bg="lightgrey", font=("Segoe UI", 20), variable=self.hex_chkbox).pack(side=tk.LEFT, padx=(20, 5))
        tk.Checkbutton(top_frame, text="hightlight", bg="lightgrey", font=("Segoe UI", 20), variable=self.hili_chkbox).pack(side=tk.LEFT, padx=(20, 5))
        tk.Checkbutton(top_frame, text="text", bg="lightgrey", font=("Segoe UI", 20), variable=self.text_chkbox).pack(side=tk.LEFT, padx=(20, 5))

    def create_plot_area(self):
        self.figure, self.ax = plt.subplots(figsize=(10, 5))
        self.ax.set_xlabel("Time (ticks)")
        self.ax.set_ylabel("Logic level")
        self.ax.set_xlim(0, 2500)
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # self.cid = self.canvas.mpl_connect("motion_notify_event", self.on_hover)

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
        
        #check if port selected
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
        self.plotter.update(None)
        self.canvas.draw()

        # Reschedule only if not stopping
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

if __name__ == "__main__":
    app = LogicAnalyzerApp()
    app.mainloop()

