import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Lock


class JammerWithPreventionSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("📡 Advanced Jammer + Prevention Simulation")
        self.lock = Lock()  # Thread safety

        # Initial variables
        self.jammer_active = False
        self.jammer_strength = 0.3  # Default blocking probability (30%)
        self.sent = 0
        self.blocked = 0
        self.success_rate_threshold = 70  # Success rate threshold
        self.check_interval = 10  # Check every N packets
        self.channel = 1  # Starting channel
        self.running = True

        # GUI Setup
        self.setup_gui()

        # Start simulation thread
        threading.Thread(target=self.simulate_packets, daemon=True).start()

    def setup_gui(self):
        """Initialize all GUI components"""
        # Status Panel
        self.status_text = tk.StringVar()
        self.status_text.set("⚡ Jammer is OFF")
        ttk.Label(self.root, textvariable=self.status_text, font=("Arial", 14)).pack(pady=10)

        # Control Buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5)

        self.toggle_button = ttk.Button(control_frame, text="Toggle Jammer", command=self.toggle_jammer)
        self.toggle_button.pack(side=tk.LEFT, padx=5)

        # Jammer Strength Slider
        ttk.Label(control_frame, text="Jammer Strength:").pack(side=tk.LEFT, padx=5)
        self.jammer_strength_slider = ttk.Scale(
            control_frame, from_=0.1, to=0.9, value=self.jammer_strength,
            command=lambda v: setattr(self, 'jammer_strength', float(v))
        )
        self.jammer_strength_slider.pack(side=tk.LEFT, padx=5)

        # Channel Display
        self.channel_label = ttk.Label(self.root, text=f"📶 Current Channel: {self.channel}",
                                       foreground="blue", font=("Arial", 12))
        self.channel_label.pack(pady=5)

        # Output Console
        self.output_box = tk.Text(self.root, height=10, width=70, state='normal')
        self.output_box.pack(pady=10, padx=10)

        # Result Label
        self.result_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.result_label.pack(pady=5)

        # Graph Setup
        self.setup_graph()

        # Exit Handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_graph(self):
        """Configure the matplotlib graph"""
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Packet Success Rate Monitoring")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Success Rate (%)")
        self.ax.set_ylim(0, 105)
        self.ax.axhline(y=self.success_rate_threshold, color='gray',
                        linestyle='--', label='Jamming Threshold')

        self.success_rate_data = []
        self.time_data = []
        self.time_counter = 0
        self.line, = self.ax.plot([], [], 'ro-', markersize=4, label='Success Rate')
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(pady=10)
        self.canvas.draw()

    def toggle_jammer(self):
        """Toggle jammer state and update UI"""
        self.jammer_active = not self.jammer_active
        state = "ON" if self.jammer_active else "OFF"
        color = "red" if self.jammer_active else "black"
        self.status_text.set(f"⚡ Jammer is {state}")
        self.channel_label.config(foreground=color)

    def simulate_packets(self):
        """Main simulation thread"""
        while self.running:
            pkt_id = random.randint(1000, 9999)
            delay = random.uniform(0.2, 0.5)

            # Packet transmission simulation
            is_blocked = self.jammer_active and random.random() < self.jammer_strength

            with self.lock:  # Thread-safe GUI updates
                if is_blocked:
                    msg = f"🚫 Packet {pkt_id} blocked (Strength: {self.jammer_strength * 100:.0f}%)"
                    self.blocked += 1
                else:
                    msg = f"✅ Packet {pkt_id} sent"
                    self.sent += 1

                self.output_box.insert(tk.END, msg + "\n")
                self.output_box.see(tk.END)
                self.output_box.update()

            time.sleep(delay)
            self.time_counter += delay
            self.update_graph()

            # Periodic jamming detection
            if (self.sent + self.blocked) % self.check_interval == 0:
                self.check_for_jamming()

    def update_graph(self):
        """Update the success rate graph"""
        total = self.sent + self.blocked
        if total > 0:
            success_rate = 100 * self.sent / total
            self.success_rate_data.append(success_rate)
            self.time_data.append(self.time_counter)

            self.line.set_data(self.time_data, self.success_rate_data)
            self.ax.set_xlim(0, max(10, self.time_counter + 2))
            self.canvas.draw()

    def check_for_jamming(self):
        """Analyze network status and trigger prevention"""
        total = self.sent + self.blocked
        success_rate = 100 * self.sent / total if total > 0 else 100

        if success_rate < self.success_rate_threshold:
            self.result_label.config(
                text=f"🔴 Jamming Detected! Success Rate: {success_rate:.1f}%",
                foreground="red"
            )
            self.prevention_action()
        else:
            self.result_label.config(
                text=f"🟢 Network Stable. Success Rate: {success_rate:.1f}%",
                foreground="green"
            )

        # Reset counters
        self.sent = 0
        self.blocked = 0

    def prevention_action(self):
        """Execute anti-jamming measures"""
        available_channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        new_channel = random.choice([ch for ch in available_channels if ch != self.channel])
        self.channel = new_channel

        with self.lock:
            self.output_box.insert(
                tk.END,
                f"🔄 Frequency hopping: Switched to Channel {self.channel}\n"
            )
            self.output_box.see(tk.END)
            self.channel_label.config(
                text=f"📶 Current Channel: {self.channel}",
                foreground="orange"  # Highlight during channel change
            )
            self.canvas.draw()

        time.sleep(1.5)  # Simulate channel switching delay
        self.channel_label.config(foreground="blue")

    def on_closing(self):
        """Cleanup on window close"""
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = JammerWithPreventionSimulator(root)
    root.mainloop()