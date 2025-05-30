import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial.tools.list_ports
from can import CANPlotter
import matplotlib
matplotlib.use("TkAgg")

class LogicAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Logic Analyzer")
        self.geometry("1600x900")

        # self.state('zoomed')
        self.configure(bg="white")

        self.create_top_panel()
        self.create_plot_area()
        self.plotter = CANPlotter()
        self.plotter.ax = self.ax
        self.plotter.canvas = self.canvas


    def create_top_panel(self):
        top_frame = tk.Frame(self, bg="black", height=100)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)

        # Port
        tk.Label(top_frame, text="Port", fg="white", bg="black", font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(20, 5))
        self.port_combo = ttk.Combobox(top_frame, values=[], width=20)
        self.port_combo.pack(side=tk.LEFT)

        # Eefresh button
        ttk.Button(top_frame, text="⟳ Refresh", command=self.update_serial_ports).pack(side=tk.LEFT, padx=5)

        # Start/Stop/Reset
        ttk.Button(top_frame, text="Start", command=self.start, width=20).pack(side=tk.LEFT, padx=10, ipady=5)
        ttk.Button(top_frame, text="Stop", command=self.stop, width=20).pack(side=tk.LEFT, padx=10, ipady=5)
        ttk.Button(top_frame, text="Reset", command=self.reset, width=20).pack(side=tk.LEFT, padx=10, ipady=5)

    def create_plot_area(self):
        self.figure, self.ax = plt.subplots(figsize=(10, 5))
        self.ax.set_title("Live CAN Frame")
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
        selected_port = self.port_combo.get()
        if "No Ports" in selected_port or not selected_port:
            print("No valid port selected.")
            return

        try:
            self.plotter.start(selected_port, baudrate=1152000)
            self.anim = FuncAnimation(self.figure, self.plotter.update, interval=100, blit=False)

            # Important: ensure the animation object stays alive
            self.canvas.draw()
            self.canvas.get_tk_widget().update_idletasks()

            print(f"Started on {selected_port}")
        except Exception as e:
            print(f"Error opening port: {e}")

    def stop(self):
        if hasattr(self, 'anim'):
            self.anim.event_source.stop()
        print("Stopped")

    def reset(self):
        print("Reset clicked")


if __name__ == "__main__":
    app = LogicAnalyzerApp()
    app.mainloop()
