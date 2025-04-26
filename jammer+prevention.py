import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
from threading import Thread, Lock
import time


class AdvancedJammerSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Jammer & Prevention Simulator")
        self.root.geometry("1200x700")

        # Simulation parameters
        self.jammer_strength = 5.0
        self.fc = 50  # Center frequency (Hz)
        self.fs = 1000  # Sampling frequency
        self.duration = 1.0  # seconds
        self.channel = 6  # WiFi channel
        self.running = False
        self.lock = Lock()

        # Data storage for success rate plot
        self.success_times = []
        self.success_rates = []
        self.start_time = 0

        # Setup GUI
        self._setup_gui()
        self._init_plots()

    def _setup_gui(self):
        """Configure all GUI components"""
        # Main frames
        control_frame = tk.Frame(self.root, bg="#e0e0e0", padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        visualization_frame = tk.Frame(self.root, bg="#f5f5f5")
        visualization_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Jammer controls
        jammer_frame = ttk.LabelFrame(control_frame, text="🛰️ Jammer Controls", padding=10)
        jammer_frame.pack(fill=tk.X, pady=5)

        ttk.Label(jammer_frame, text="Jamming Type:").grid(row=0, column=0, sticky="w")
        self.jammer_type_var = tk.StringVar(value="Noise")
        self.jammer_type_menu = ttk.Combobox(jammer_frame, textvariable=self.jammer_type_var,
                                             values=["Noise", "Tone", "Pulsed", "Sweep"])
        self.jammer_type_menu.grid(row=0, column=1, pady=5, sticky="ew")

        ttk.Label(jammer_frame, text="Jammer Strength:").grid(row=1, column=0, sticky="w")
        self.strength_slider = ttk.Scale(jammer_frame, from_=0, to=10, value=self.jammer_strength,
                                         command=lambda v: setattr(self, 'jammer_strength', float(v)))
        self.strength_slider.grid(row=1, column=1, pady=5, sticky="ew")
        self.strength_label = ttk.Label(jammer_frame, text=f"Current: {self.jammer_strength:.1f}")
        self.strength_label.grid(row=2, column=1, sticky="e")

        # Prevention controls
        prev_frame = ttk.LabelFrame(control_frame, text="🛡️ Prevention Methods", padding=10)
        prev_frame.pack(fill=tk.X, pady=10)

        self.prev_method_var = tk.StringVar(value="Channel Hopping")
        ttk.Radiobutton(prev_frame, text="Channel Hopping", variable=self.prev_method_var,
                        value="Channel Hopping").pack(anchor="w", pady=2)
        ttk.Radiobutton(prev_frame, text="Spread Spectrum", variable=self.prev_method_var,
                        value="Spread Spectrum").pack(anchor="w", pady=2)
        ttk.Radiobutton(prev_frame, text="Adaptive Filter", variable=self.prev_method_var,
                        value="Adaptive Filter").pack(anchor="w", pady=2)

        # Action buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Start Simulation", command=self.start_simulation).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Apply Prevention", command=self.apply_prevention).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Stop", command=self.stop_simulation).pack(fill=tk.X, pady=5)

        # Console
        console_frame = ttk.LabelFrame(control_frame, text="📝 Console Output", padding=10)
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console = tk.Text(console_frame, height=15, width=40, wrap="word",
                               bg="black", fg="white", font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True)

        # Visualization area
        self.fig = plt.Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=visualization_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status bar
        self.status_var = tk.StringVar(value="🟢 Ready")
        ttk.Label(control_frame, textvariable=self.status_var,
                  font=("Arial", 10), background="#e0e0e0").pack(side=tk.BOTTOM, fill=tk.X)

    def _init_plots(self):
        """Initialize the matplotlib plots"""
        self.fig.clf()

        # Time domain plot
        self.ax_time = self.fig.add_subplot(221)
        self.ax_time.set_title("Time Domain")
        self.ax_time.set_xlabel("Time (s)")
        self.ax_time.set_ylabel("Amplitude")
        self.line_time, = self.ax_time.plot([], [], 'b-', label="Original")
        self.line_jammed, = self.ax_time.plot([], [], 'r-', label="Jammed", alpha=0.7)
        self.ax_time.legend()

        # Frequency domain plot
        self.ax_freq = self.fig.add_subplot(222)
        self.ax_freq.set_title("Frequency Domain")
        self.ax_freq.set_xlabel("Frequency (Hz)")
        self.ax_freq.set_ylabel("Magnitude")
        self.line_freq, = self.ax_freq.plot([], [], 'g-')

        # Success rate plot
        self.ax_success = self.fig.add_subplot(212)
        self.ax_success.set_title("Success Rate Over Time")
        self.ax_success.set_xlabel("Time (s)")
        self.ax_success.set_ylabel("Success Rate (%)")
        self.ax_success.set_ylim(0, 110)
        self.line_success, = self.ax_success.plot([], [], 'm-')
        self.ax_success.axhline(y=70, color='r', linestyle='--', label='Threshold')
        self.ax_success.legend()

        self.canvas.draw()

    def _generate_signal(self, t):
        """Generate the signal with current jamming type"""
        signal = np.sin(2 * np.pi * self.fc * t)

        if self.jammer_type_var.get() == "Noise":
            jammer = self.jammer_strength * np.random.randn(len(t))
        elif self.jammer_type_var.get() == "Tone":
            jammer = self.jammer_strength * np.sin(2 * np.pi * self.fc * t)
        elif self.jammer_type_var.get() == "Pulsed":
            jammer = np.zeros(len(t))
            jammer[::50] = self.jammer_strength * 2
        else:  # Sweep
            jammer = self.jammer_strength * np.sin(2 * np.pi * (50 + 30 * t) * t)

        return signal, jammer

    def start_simulation(self):
        if not self.running:
            self.running = True
            self.status_var.set("🟡 Simulating...")
            self.success_times = []
            self.success_rates = []
            self.start_time = time.time()
            Thread(target=self._run_simulation, daemon=True).start()

    def stop_simulation(self):
        self.running = False
        self.status_var.set("🟢 Ready")

    def _run_simulation(self):
        """Main simulation loop"""
        t = np.linspace(0, self.duration, int(self.fs * self.duration))

        while self.running:
            try:
                # Generate signals
                signal, jammer = self._generate_signal(t)
                jammed_signal = signal + jammer

                # Calculate metrics
                snr = np.mean(signal ** 2) / (np.mean(jammer ** 2) + 1e-6)
                success_rate = 100 * np.clip(snr / 10, 0, 1)
                current_time = time.time() - self.start_time

                # Update data storage
                with self.lock:
                    self.success_times.append(current_time)
                    self.success_rates.append(success_rate)

                    # Keep only the last 100 points for performance
                    if len(self.success_times) > 100:
                        self.success_times.pop(0)
                        self.success_rates.pop(0)

                # Update plots
                self._update_plots(t, signal, jammed_signal)

                # Update console
                self._log(f"SNR: {snr:.2f} dB | Success: {success_rate:.1f}% | Channel: {self.channel}")

                time.sleep(0.5)

            except Exception as e:
                self._log(f"Error: {str(e)}")
                break

        self.status_var.set("🟢 Simulation stopped")

    def _update_plots(self, t, signal, jammed_signal):
        """Update all plots"""
        # Time domain
        self.line_time.set_data(t, signal)
        self.line_jammed.set_data(t, jammed_signal)
        self.ax_time.relim()
        self.ax_time.autoscale_view()

        # Frequency domain
        freqs = np.fft.fftfreq(len(t), 1 / self.fs)[:len(t) // 2]
        fft_signal = np.abs(np.fft.fft(jammed_signal))[:len(t) // 2]
        self.line_freq.set_data(freqs, fft_signal)
        self.ax_freq.relim()
        self.ax_freq.autoscale_view()

        # Success rate (using thread-safe data access)
        with self.lock:
            self.line_success.set_data(self.success_times, self.success_rates)

        self.ax_success.relim()
        self.ax_success.autoscale_view()

        self.canvas.draw()

    def apply_prevention(self):
        """Apply the selected prevention method"""
        method = self.prev_method_var.get()

        if method == "Channel Hopping":
            new_channel = random.choice([ch for ch in range(1, 12) if ch != self.channel])
            self.channel = new_channel
            self._log(f"🔄 Channel hopping to {self.channel}")

        elif method == "Spread Spectrum":
            self.fc = random.choice([40, 45, 50, 55, 60])
            self._log(f"📡 Spread spectrum applied. New center freq: {self.fc} Hz")

        elif method == "Adaptive Filter":
            self.jammer_strength *= 0.7
            self.strength_slider.set(self.jammer_strength)
            self.strength_label.config(text=f"Current: {self.jammer_strength:.1f}")
            self._log(f"🛡️ Adaptive filter reduced jammer strength to {self.jammer_strength:.1f}")

    def _log(self, message):
        """Add message to console with timestamp"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedJammerSimulator(root)
    root.mainloop()