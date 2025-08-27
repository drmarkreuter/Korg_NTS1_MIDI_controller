import tkinter as tk
from tkinter import ttk
import pygame.midi
import threading
import time

class KorgNTS1Controller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Korg NTS1 MIDI Controller")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize pygame MIDI
        pygame.midi.init()
        
        # MIDI settings
        self.midi_out = None
        self.midi_channel = 0  # 0-15 (Channel 1-16)
        
        # Store current CC values to avoid duplicate sends
        self.cc_values = {}
        
        # Create the UI
        self.create_midi_settings()
        self.create_controls()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_midi_settings(self):
        """Create MIDI device and channel selection controls"""
        settings_frame = tk.Frame(self.root, bg='#f0f0f0')
        settings_frame.pack(pady=10, padx=20, fill='x')
        
        # MIDI Device selection
        tk.Label(settings_frame, text="MIDI Device:", bg='#f0f0f0', font=('Arial', 10)).grid(row=0, column=0, padx=5, sticky='w')
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(settings_frame, textvariable=self.device_var, state="readonly", width=30)
        self.device_combo.grid(row=0, column=1, padx=5)
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
        
        # Refresh devices button
        refresh_btn = tk.Button(settings_frame, text="Refresh", command=self.refresh_devices)
        refresh_btn.grid(row=0, column=2, padx=5)
        
        # MIDI Channel selection
        tk.Label(settings_frame, text="MIDI Channel:", bg='#f0f0f0', font=('Arial', 10)).grid(row=0, column=3, padx=5, sticky='w')
        
        self.channel_var = tk.StringVar(value="1")
        channel_combo = ttk.Combobox(settings_frame, textvariable=self.channel_var, 
                                   values=[str(i) for i in range(1, 17)], 
                                   state="readonly", width=5)
        channel_combo.grid(row=0, column=4, padx=5)
        channel_combo.bind('<<ComboboxSelected>>', self.on_channel_selected)
        
        # Connection status
        self.status_label = tk.Label(settings_frame, text="Status: Not Connected", 
                                   bg='#f0f0f0', font=('Arial', 10), fg='red')
        self.status_label.grid(row=0, column=5, padx=20)
        
        # Refresh device list on startup
        self.refresh_devices()
    
    def create_controls(self):
        """Create all the synthesizer control sections"""
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Top row: Osc, Amp Env, Filter, Tremolo
        top_frame = tk.Frame(main_frame, bg='#f0f0f0')
        top_frame.pack(fill='x', pady=5)
        
        self.create_osc_section(top_frame)
        self.create_amp_env_section(top_frame)
        self.create_filter_section(top_frame)
        self.create_tremolo_section(top_frame)
        
        # Bottom row: Modulation, Delay, Reverb
        bottom_frame = tk.Frame(main_frame, bg='#f0f0f0')
        bottom_frame.pack(fill='x', pady=5)
        
        self.create_modulation_section(bottom_frame)
        self.create_delay_section(bottom_frame)
        self.create_reverb_section(bottom_frame)
    
    def create_section(self, parent, title, controls, bg_color='#90EE90'):
        """Create a control section with sliders"""
        frame = tk.Frame(parent, bg=bg_color, relief='ridge', bd=2)
        frame.pack(side='left', padx=5, pady=5, fill='both', expand=True)
        
        # Section title
        title_label = tk.Label(frame, text=title, bg='#FFA500', font=('Arial', 12, 'bold'), relief='raised', bd=1)
        title_label.pack(fill='x', pady=2, padx=2)
        
        # Controls container
        controls_frame = tk.Frame(frame, bg=bg_color)
        controls_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        for i, (label, cc, default) in enumerate(controls):
            # Create vertical slider with label
            control_frame = tk.Frame(controls_frame, bg=bg_color)
            control_frame.grid(row=0, column=i, padx=10, pady=5)
            
            # Value label
            value_label = tk.Label(control_frame, text=str(default), bg='white', width=4, relief='sunken')
            value_label.pack(pady=2)
            
            # Slider
            slider = tk.Scale(control_frame, from_=127, to=0, orient='vertical', 
                            length=200, width=20, bg='#4a4a4a', fg='white',
                            highlightthickness=0, troughcolor='#2a2a2a',
                            command=lambda val, cc=cc, lbl=value_label: self.on_slider_change(cc, val, lbl))
            slider.set(default)
            slider.pack()
            
            # Control label
            control_label = tk.Label(control_frame, text=label, bg='#FFA500', font=('Arial', 9, 'bold'), 
                                   relief='raised', bd=1, width=8)
            control_label.pack(pady=2)
    
    def create_osc_section(self, parent):
        controls = [
            ("Wave-shape\nAmount", 54, 0),
            ("LFO\nRate", 24, 0),
            ("LFO\nDepth", 26, 0)
        ]
        self.create_section(parent, "Osc", controls)
    
    def create_amp_env_section(self, parent):
        controls = [
            ("Attack", 16, 0),
            ("Release", 19, 64)
        ]
        self.create_section(parent, "Amp Env", controls)
    
    def create_filter_section(self, parent):
        controls = [
            ("Cutoff", 43, 127),
            ("Resonance", 44, 0)
        ]
        self.create_section(parent, "Filter", controls)
    
    def create_tremolo_section(self, parent):
        controls = [
            ("Rate", 20, 0),
            ("Depth", 21, 0)
        ]
        self.create_section(parent, "Tremolo", controls)
    
    def create_modulation_section(self, parent):
        controls = [
            ("Time", 28, 0),
            ("Depth", 29, 0)
        ]
        self.create_section(parent, "Modulation", controls)
    
    def create_delay_section(self, parent):
        controls = [
            ("Time", 30, 0),
            ("Depth", 31, 0),
            ("Mix", 33, 0)
        ]
        self.create_section(parent, "Delay", controls)
    
    def create_reverb_section(self, parent):
        controls = [
            ("Time", 34, 0),
            ("Depth", 35, 0),
            ("Mix", 36, 0)
        ]
        self.create_section(parent, "Reverb", controls)
    
    def refresh_devices(self):
        """Refresh the list of available MIDI devices"""
        devices = []
        print(f"Scanning {pygame.midi.get_count()} MIDI devices...")
        
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            interface = info[0].decode('utf-8')
            device_name = info[1].decode('utf-8')
            is_input = info[2]
            is_output = info[3]
            opened = info[4]
            
            print(f"Device {i}: {device_name} (Interface: {interface}, Output: {is_output}, Opened: {opened})")
            
            if is_output:  # Only show output devices
                status = " [IN USE]" if opened else ""
                devices.append(f"{i}: {device_name}{status}")
        
        self.device_combo['values'] = devices
        
        if devices:
            self.device_combo.current(0)
            print(f"Found {len(devices)} output devices")
        else:
            print("No MIDI output devices found!")
            self.status_label.config(text="Status: No MIDI Devices Found", fg='red')
    
    def on_device_selected(self, event):
        """Handle MIDI device selection"""
        if self.midi_out:
            self.midi_out.close()
            self.midi_out = None
        
        selection = self.device_var.get()
        if selection:
            # Extract device ID (handle "[IN USE]" suffix)
            device_id = int(selection.split(':')[0])
            device_name = selection.split(': ', 1)[1].replace(' [IN USE]', '')
            
            print(f"Attempting to connect to device {device_id}: {device_name}")
            
            try:
                self.midi_out = pygame.midi.Output(device_id)
                self.status_label.config(text=f"Status: Connected to {device_name}", fg='green')
                print(f"Successfully connected to {device_name}")
            except Exception as e:
                error_msg = str(e)
                self.status_label.config(text=f"Status: Error - {error_msg}", fg='red')
                print(f"Failed to connect to {device_name}: {error_msg}")
                
                # Suggest solutions based on error type
                if "Device unavailable" in error_msg or "in use" in error_msg.lower():
                    print("Suggestion: The device might be in use by another application (like your DAW)")
                elif "Invalid device" in error_msg:
                    print("Suggestion: Try refreshing the device list")

    
    def on_channel_selected(self, event):
        """Handle MIDI channel selection"""
        self.midi_channel = int(self.channel_var.get()) - 1  # Convert to 0-15
    
    def on_slider_change(self, cc, value, label):
        """Handle slider value changes"""
        int_value = int(float(value))
        label.config(text=str(int_value))
        
        # Only send MIDI if value actually changed
        if self.cc_values.get(cc) != int_value:
            self.cc_values[cc] = int_value
            self.send_cc(cc, int_value)
    
    def send_cc(self, cc, value):
        """Send MIDI CC message"""
        if self.midi_out:
            try:
                # MIDI CC message: [status_byte, cc_number, value]
                # Status byte: 0xB0 + channel (0-15)
                status_byte = 0xB0 + self.midi_channel
                self.midi_out.write_short(status_byte, cc, value)
            except Exception as e:
                print(f"Error sending MIDI: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        if self.midi_out:
            self.midi_out.close()
        pygame.midi.quit()
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = KorgNTS1Controller()
    app.run()