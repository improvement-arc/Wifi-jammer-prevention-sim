import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class FixedJammerSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("📡 Fixed Jammer Simulator")
        self.lock = threading.Lock()

        # Signal parameters (adjusted for better FFT visualization)
        self.sample_rate = 1000  # Hz
        self.duration = 1.0  # seconds
        self.n_samples = 1024  # Increased for better frequency resolution
        self.t = np.linspace(0, self.duration, self.n_samples, endpoint=False)
        self.center_freq = 100  # Hz

        # Jamming parameters
        self.simulation_params = {
            "None": {"block_prob": 0.0, "spectrum_func": self._clean_spectrum},
            "Noise": {"block_prob": 0.6, "spectrum_func": self._noise_spectrum},
            "Repeater": {"block_prob": 0.4, "spectrum_func": self._repeater_spectrum},
            "Tone": {"block_prob": 0.7, "spectrum_func": self._tone_spectrum},
            "Pulsed": {"block_prob": 0.5, "spectrum_func": self._pulsed_spectrum}
        }

        # Initialize state
        self.jamming_mode = tk.StringVar(value="None")
        self.sent = 0
        self.blocked = 0
        self.time_counter = 0
        self.running = True

        # Setup GUI
        self.setup_gui()
        threading.Thread(target=self.simulate, daemon=True).start()

    # Spectrum generation methods -----------------------------------------------
    def _clean_spectrum(self):
        """Clean signal spectrum (sine wave)"""
        return np.sin(2 * np.pi * self.center_freq * self.t)

    def _noise_spectrum(self):
        """White noise jamming spectrum"""
        return np.random.normal(0, 1, self.n_samples)

    def _repeater_spectrum(self):
        """Repeater jamming signature"""
        return (np.sin(2 * np.pi * 50 * self.t) +
                np.sin(2 * np.pi * 150 * self.t)) * 0.7

    def _tone_spectrum(self):
        """Single tone jamming"""
        return 1.5 * np.sin(2 * np.pi * self.center_freq * self.t)

    def _pulsed_spectrum(self):
        """Pulsed jamming signal"""
        pulse = np.zeros(self.n_samples)
        pulse[::100] = 2.0  # Pulse every 100 samples
        return pulse

    # GUI setup ----------------------------------------------------------------
    def setup_gui(self):
        """Initialize the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Jamming Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=5)

        # Jamming Mode Selector
        ttk.Label(control_frame, text="Technique:").pack(side=tk.LEFT)
        self.jamming_selector = ttk.Combobox(
            control_frame,
            textvariable=self.jamming_mode,
            values=list(self.simulation_params.keys()),
            state="readonly"
        )
        self.jamming_selector.pack(side=tk.LEFT, padx=5)

        # Status Display
        self.status_label = ttk.Label(
            control_frame,
            text="Status: 🟢 No Jamming",
            font=("Arial", 11)
        )
        self.status_label.pack(side=tk.RIGHT)

        # Output Console
        self.output_box = tk.Text(
            main_frame,
            height=8,
            width=80,
            state='normal'
        )
        self.output_box.pack(pady=10)

        # Visualization
        self.setup_visualization(main_frame)

    def setup_visualization(self, parent):
        """Configure the dual plots"""
        fig_frame = ttk.Frame(parent)
        fig_frame.pack(fill=tk.BOTH, expand=True)

        # Success Rate Plot
        self.fig1, self.ax1 = plt.subplots(figsize=(7, 3))
        self.success_line, = self.ax1.plot([], [], 'g-', label="Success Rate")
        self.ax1.set_title("📈 Packet Success Rate")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Rate (%)")
        self.ax1.set_ylim(0, 110)
        self.ax1.axhline(y=50, color='r', linestyle='--', label='Threshold')
        self.ax1.legend()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=fig_frame)
        self.canvas1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fixed Frequency Spectrum Plot
        self.fig2, self.ax2 = plt.subplots(figsize=(7, 3))
        self.freq_line, = self.ax2.plot([], [], 'b-', label="Spectrum")
        self.ax2.set_title("🌐 Frequency Domain (FFT)")
        self.ax2.set_xlabel("Frequency (Hz)")
        self.ax2.set_ylabel("Magnitude")
        self.ax2.set_xlim(0, 200)  # Focus on 0-200Hz range
        self.ax2.grid(True)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=fig_frame)
        self.canvas2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Simulation loop ----------------------------------------------------------
    def simulate(self):
        """Main simulation thread"""
        while self.running:
            try:
                mode = self.jamming_mode.get()
                params = self.simulation_params[mode]

                # Packet transmission
                pkt_id = random.randint(1000, 9999)
                blocked = random.random() < params["block_prob"]

                # Update counters and UI
                with self.lock:
                    if blocked:
                        self.blocked += 1
                        msg = f"🚫 Packet {pkt_id} BLOCKED ({mode})"
                    else:
                        self.sent += 1
                        msg = f"✅ Packet {pkt_id} SENT"

                    self.output_box.insert(tk.END, msg + "\n")
                    self.output_box.see(tk.END)

                # Generate and analyze signal
                time_domain = params["spectrum_func"]()
                freq_domain = np.abs(np.fft.fft(time_domain))[:self.n_samples // 2]
                freqs = np.fft.fftfreq(self.n_samples, 1 / self.sample_rate)[:self.n_samples // 2]

                # Update visualizations
                self.time_counter += 0.4
                total = self.sent + self.blocked

                if total > 0:
                    success_rate = 100 * self.sent / total

                    # Update success plot
                    if not hasattr(self, 'success_data'):
                        self.success_data = []
                        self.time_data = []

                    self.success_data.append(success_rate)
                    self.time_data.append(self.time_counter)

                    self.success_line.set_data(self.time_data, self.success_data)
                    self.ax1.relim()
                    self.ax1.autoscale_view()

                # Update frequency plot (FIXED)
                self.freq_line.set_data(freqs, freq_domain)
                self.ax2.relim()
                self.ax2.autoscale_view()

                # Update status
                status_map = {
                    "None": ("🟢", "No Jamming"),
                    "Noise": ("🔴", "Noise Jamming"),
                    "Repeater": ("🟠", "Repeater Jamming"),
                    "Tone": ("🟣", "Tone Jamming"),
                    "Pulsed": ("⚡", "Pulsed Jamming")
                }
                icon, text = status_map[mode]

                with self.lock:
                    self.status_label.config(text=f"Status: {icon} {text}")
                    self.canvas1.draw()
                    self.canvas2.draw()

                time.sleep(0.4)

            except Exception as e:
                print(f"Simulation error: {e}")
                break

    def on_closing(self):
        """Clean shutdown"""
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FixedJammerSimulator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()