import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import serial
import sys
import time

# --- Sovereign HUD v2: Matplotlib 3D Edition ---
# Architecture: 13-axis Cartesian Manifold
# Interaction: WASD Artery Link

class SovereignHUD:
    def __init__(self, port):
        self.port = port
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.01)
        except Exception as e:
            print(f"ERROR: Could not open port {port}: {e}")
            sys.exit(1)

        self.energy = 0
        self.active_axis = 0
        self.is_booting = False

        # Setup 3D Plot
        plt.ion()
        self.fig = plt.figure(figsize=(10, 8), facecolor='#050a0f')
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#050a0f')
        self.fig.canvas.manager.set_window_title("SPU-13 SOVEREIGN MANIFOLD [HUD v2.1]")

        # Connect Keyboard
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        # Manifold DNA (13 Nodes)
        self.angles = np.linspace(0, 2*np.pi, 13, endpoint=False)
        self.nodes = np.column_stack([np.cos(self.angles), np.sin(self.angles), np.zeros(13)])

    def on_key(self, event):
        if event.key == 'w': self.ser.write(b'w')
        if event.key == 's': self.ser.write(b's')
        if event.key == 'a': self.ser.write(b'a')
        if event.key == 'd': self.ser.write(b'd')
        if event.key == ' ': self.ser.write(b' ')

    def update_telemetry(self):
        if self.ser.in_waiting > 0:
            try:
                line = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                if "B:" in line: self.is_booting = True
                if "Q:" in line: self.is_booting = False
                
                sig = "B:" if self.is_booting else "Q:"
                if sig in line:
                    data = line.split(sig)[-1].split()
                    if len(data) >= 2:
                        self.energy = int(data[0], 16)
                        a_str = data[1].split("A:")[-1]
                        self.active_axis = int(a_str, 16)
            except:
                pass

    def run(self):
        print("HUD v2.1 (Matplotlib) ACTIVE.")
        print("Controls: WASD to rotate, SPACE to reset.")
        
        while plt.fignum_exists(self.fig.number):
            self.update_telemetry()
            
            self.ax.clear()
            self.ax.set_facecolor('#050a0f')
            
            # Draw Orbital Lines
            for i in range(13):
                p1 = self.nodes[i]
                p2 = self.nodes[(i+1)%13]
                
                color = '#00ffff' if i != self.active_axis else '#ff3232'
                lw = 1 if i != self.active_axis else 3
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color=color, linewidth=lw)
                
                # Label Node
                if i == self.active_axis:
                    self.ax.text(p1[0], p1[1], p1[2], f"Axis {i}", color='white')

            # Draw Status
            status = "INHALING..." if self.is_booting else "ACTIVE"
            title_color = 'yellow' if self.is_booting else 'cyan'
            self.ax.set_title(f"STATUS: {status} | ENERGY: 0x{self.energy:08X}", color=title_color, fontsize=14)
            
            # Force 3D limits
            self.ax.set_xlim(-1.5, 1.5); self.ax.set_ylim(-1.5, 1.5); self.ax.set_zlim(-1.5, 1.5)
            self.ax.axis('off')
            
            # Cinematic Spin
            self.ax.view_init(elev=20, azim=time.time()*20 % 360)
            
            plt.pause(0.01)

if __name__ == "__main__":
    port = "/dev/tty.usbserial-20250303171"
    if len(sys.argv) > 1: port = sys.argv[1]
    hud = SovereignHUD(port)
    hud.run()
