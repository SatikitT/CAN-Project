import tkinter as tk
from tkinter import ttk, filedialog

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

        # self.state('zoomed')
        self.configure(bg="white")
        self.canvas = None 

        self.stop_event   = threading.Event()
        self.serial_thr   = None

        self.create_top_panel()
        self.create_plot_area()
        self.get_serial_ports()
        self.update_serial_ports()

        self.plotter = Plotter()
        self.plotter.ax = self.ax        

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_top_panel(self):
        top_frame = tk.Frame(self, bg="black", height=100)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)

        # Port
        tk.Label(top_frame, text="Port", fg="white", bg="black", font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))
        self.port_combo = ttk.Combobox(top_frame, values=[], width=20)
        self.port_combo.pack(side=tk.LEFT)

        # Eefresh button
        ttk.Button(top_frame, text="⟳ Refresh", command=self.update_serial_ports).pack(side=tk.LEFT, padx=10, ipady=5)

        # Start/Stop/Reset
        ttk.Button(top_frame, text="Start", command=self.start, width=20).pack(side=tk.LEFT, padx=10, ipady=5)
        ttk.Button(top_frame, text="Stop", command=self.stop, width=20).pack(side=tk.LEFT, padx=10, ipady=5)
        ttk.Button(top_frame, text="Reset", command=self.reset, width=20).pack(side=tk.LEFT, padx=10, ipady=5)

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
            # self.plotter.start(selected_port, baudrate=1152000)

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
        self.after(READ_INTERVAL, self.periodic_update)

    def stop(self):
        if hasattr(self, 'anim'):
            self.anim.event_source.stop()
        print("Stopped")

    def reset(self):
        print("Reset clicked")

    def on_close(self):
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = LogicAnalyzerApp()
    app.mainloop()

