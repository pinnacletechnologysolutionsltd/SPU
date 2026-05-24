import pygame
import serial
import time
import sys
import math

# --- Sovereign HUD v2: 3D Manifold Engine ---
# Architecture: 13-axis Projected Wireframe
# Interaction: Bi-directional Artery Link (UART)

class SovereignHUD:
    def __init__(self, port):
        pygame.init()
        self.width, self.height = 1024, 768
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("SPU-13 SOVEREIGN MANIFOLD [HUD v2.0]")
        self.clock = pygame.time.Clock()
        
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.01)
        except Exception as e:
            print(f"ERROR: Could not open port {port}: {e}")
            sys.exit(1)

        self.font = pygame.font.SysFont("Courier New", 20, bold=True)
        self.running = True
        self.energy = 0
        self.active_axis = 0
        self.is_booting = False
        
        # 3D State
        self.rot_x = 0
        self.rot_y = 0
        
        # Manifold DNA (13 Nodes)
        self.nodes = []
        for i in range(13):
            angle = (i / 13.0) * math.pi * 2
            x = math.cos(angle)
            y = math.sin(angle)
            z = 0
            self.nodes.append([x, y, z])

    def project(self, node):
        # Rotate 3D
        x, y, z = node
        
        # X Rotation
        ny = y * math.cos(self.rot_x) - z * math.sin(self.rot_x)
        nz = y * math.sin(self.rot_x) + z * math.cos(self.rot_x)
        y, z = ny, nz
        
        # Y Rotation
        nx = x * math.cos(self.rot_y) + z * math.sin(self.rot_y)
        nz = -x * math.sin(self.rot_y) + z * math.cos(self.rot_y)
        x, z = nx, nz
        
        # Projection
        factor = 300 / (z + 4)
        px = x * factor + self.width // 2
        py = -y * factor + self.height // 2
        return int(px), int(py)

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

    def draw(self):
        self.screen.fill((5, 10, 15)) # Deep space
        
        # Draw Orbital Cage
        for i in range(13):
            p1 = self.project(self.nodes[i])
            p2 = self.project(self.nodes[(i+1)%13])
            
            color = (0, 255, 255) if i != self.active_axis else (255, 50, 50)
            width = 2 if i != self.active_axis else 5
            pygame.draw.line(self.screen, color, p1, p2, width)
            
            # Label Node
            label = self.font.render(str(i), True, (100, 100, 100))
            self.screen.blit(label, (p1[0]+10, p1[1]+10))

        # Draw Energy Core
        core_radius = 50 + (self.energy % 100) // 2
        core_color = (0, 255, 100) if not self.is_booting else (255, 200, 0)
        pygame.draw.circle(self.screen, core_color, (self.width//2, self.height//2), core_radius, 2)
        
        # Status Text
        status = "INHALING..." if self.is_booting else "ACTIVE"
        color = (255, 200, 0) if self.is_booting else (0, 255, 100)
        
        txt_status = self.font.render(f"STATUS: {status}", True, color)
        txt_energy = self.font.render(f"QUADRANCE: 0x{self.energy:08X}", True, (255, 255, 255))
        txt_axis   = self.font.render(f"ACTIVE AXIS: {self.active_axis}", True, (255, 255, 255))
        
        self.screen.blit(txt_status, (20, 20))
        self.screen.blit(txt_energy, (20, 50))
        self.screen.blit(txt_axis,   (20, 80))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Handle Keyboard (Artery Inbound)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w: self.ser.write(b'w')
                    if event.key == pygame.K_s: self.ser.write(b's')
                    if event.key == pygame.K_a: self.ser.write(b'a')
                    if event.key == pygame.K_d: self.ser.write(b'd')
                    if event.key == pygame.K_SPACE: self.ser.write(b' ')

            self.update_telemetry()
            self.rot_y += 0.01 # Slow cinematic spin
            self.draw()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    port = "/dev/tty.usbserial-20250303171"
    if len(sys.argv) > 1: port = sys.argv[1]
    hud = SovereignHUD(port)
    hud.run()
