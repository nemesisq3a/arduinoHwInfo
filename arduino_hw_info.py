#!/usr/bin/env python3
"""
Hardware Monitor for Arduino on Linux
This script replicates the functionality of the C# ArduinoHwInfo application on Linux.
It collects hardware information and sends it to an Arduino via serial communication.
"""

import time
import serial
import subprocess
import re
import threading
import signal
import sys
from pathlib import Path


class HardwareMonitor:
    def __init__(self):
        self.cpu_temps = [0] * 16
        self.cpu_loads = [0] * 16
        self.cpu_freqs = [0] * 8
        self.gpu_temp = 0
        self.gpu_core_clock = 0
        self.gpu_mem_clock = 0
        self.gpu_load = 0
        self.gpu_vram_used = 0
        self.gpu_vram_total = 0
        self.gpu_vram_percentage = 0
        self.cpu_package_temp = 0
        self.cpu_total_load = 0
        self.fps = 0  # Placeholder - FPS monitoring is complex on Linux
        self.ghz_avg = 0.0
        
        # Store previous CPU stats for load calculation
        self.prev_cpu_stats = {}
        
        # For FPS, we might implement a simple frame counter later
        self.running = True

    def get_cpu_temperature_sensors(self):
        """Get CPU temperature using the 'sensors' command from lm-sensors."""
        try:
            # Run 'sensors' command to get hardware temperatures
            result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
            output = result.stdout
            
            # Prioritize specific sensors, especially Tctl for AMD CPUs
            # Look for Tctl first as it's the requested temperature
            tctl_match = re.search(r'Tctl:.*\+([0-9]+\.[0-9]+)', output)
            if tctl_match:
                return float(tctl_match.group(1))
            
            # Look for CPU temperature patterns in the output
            # Common patterns include: Core 0, Core 1, Package, CPU Temp, etc.
            temp_patterns = [
                r'Package.*:.*\+([0-9]+\.[0-9]+)',  # Package temperature
                r'Core [0-9]+:.*\+([0-9]+\.[0-9]+)',  # Core temperatures
                r'CPU Temp.*:.*\+([0-9]+\.[0-9]+)',  # CPU temperature
                r'cpu_thermal.*:.*\+([0-9]+\.[0-9]+)',  # CPU thermal
                r'acpi.*:.*\+([0-9]+\.[0-9]+)',  # ACPI thermal
                r'CPUTIN:.*\+([0-9]+\.[0-9]+)',  # CPU temperature from hardware monitor
                r'TSI0_TEMP:.*\+([0-9]+\.[0-9]+)',  # Additional thermal sensors
                r'TSI1_TEMP:.*\+([0-9]+\.[0-9]+)',  # Additional thermal sensors
            ]
            
            all_temps = []
            for pattern in temp_patterns:
                matches = re.findall(pattern, output)
                if matches:
                    # Add all found temperatures to the list
                    temps = [float(temp) for temp in matches]
                    all_temps.extend(temps)
            
            if all_temps:
                # Return the highest temperature found from remaining sensors
                return max(all_temps)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 'sensors' command not available or failed
            pass
        except Exception:
            pass
        
        return None

    def get_cpu_temperature_thermal_zones(self):
        """Get CPU temperature from thermal zones in /sys/class/thermal/."""
        try:
            cpu_temp = 0
            for i in range(20):  # Check first 20 thermal zones
                temp_path = f"/sys/class/thermal/thermal_zone{i}/temp"
                type_path = f"/sys/class/thermal/thermal_zone{i}/type"
                
                if Path(temp_path).exists() and Path(type_path).exists():
                    with open(type_path, 'r') as f:
                        type_name = f.read().strip()
                    
                    # Check for CPU-related thermal zones
                    if any(keyword in type_name.lower() for keyword in ['cpu', 'package', 'core']):
                        with open(temp_path, 'r') as f:
                            temp = int(f.read().strip()) / 1000.0  # Convert from millidegrees
                            cpu_temp = max(cpu_temp, temp)
            
            return cpu_temp if cpu_temp > 0 else None
        except Exception:
            return None

    def get_cpu_temperature(self):
        """Get CPU temperature using multiple methods."""
        # Try sensors command first (more reliable)
        temp = self.get_cpu_temperature_sensors()
        if temp is not None and temp > 0:
            return temp
        
        # Fallback to thermal zones
        temp = self.get_cpu_temperature_thermal_zones()
        if temp is not None and temp > 0:
            return temp
        
        # If all methods fail, return 0
        return 0

    def get_cpu_info(self):
        """Get CPU information including temperatures, loads, and frequencies."""
        # Get CPU temperature
        self.cpu_package_temp = self.get_cpu_temperature()

        # Get CPU frequencies
        try:
            for i in range(8):  # Check up to 8 CPU cores for frequency
                freq_path = f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq"
                if Path(freq_path).exists():
                    with open(freq_path, 'r') as f:
                        freq = int(f.read().strip()) / 1000000.0  # Convert to GHz
                        if i < len(self.cpu_freqs):
                            self.cpu_freqs[i] = freq  # Keep as float to preserve decimal values
        except Exception:
            pass

        # Calculate average GHz
        active_freqs = [f for f in self.cpu_freqs if f > 0]
        if active_freqs:
            self.ghz_avg = round(sum(active_freqs) / len(active_freqs), 1)

    def get_cpu_loads(self):
        """Get CPU loads for individual cores and total CPU."""
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            cpu_lines = [line for line in lines if line.startswith('cpu') and line[3] != ' ']
            
            # Process total CPU line (first line)
            if len(cpu_lines) > 0:
                parts = cpu_lines[0].split()  # Total CPU line (cpu)
                if len(parts) >= 5:
                    cpu_name = parts[0]
                    user = int(parts[1])
                    nice = int(parts[2])
                    system = int(parts[3])
                    idle = int(parts[4])
                    
                    total = user + nice + system + idle
                    total_idle = idle
                    
                    # Calculate total CPU load
                    if cpu_name in self.prev_cpu_stats:
                        prev_total, prev_idle = self.prev_cpu_stats[cpu_name]
                        total_diff = total - prev_total
                        idle_diff = total_idle - prev_idle
                        
                        if total_diff != 0:
                            cpu_load = 100.0 * (total_diff - idle_diff) / total_diff
                            self.cpu_total_load = round(cpu_load, 0)
                    
                    self.prev_cpu_stats[cpu_name] = (total, total_idle)
            
            # Process individual CPU cores (cpu0, cpu1, etc.)
            for i, line in enumerate(cpu_lines[1:17]):  # cpu0 to cpu15 (or available cores)
                if i < 16:
                    parts = line.split()
                    if len(parts) >= 5:
                        cpu_name = parts[0]
                        user = int(parts[1])
                        nice = int(parts[2])
                        system = int(parts[3])
                        idle = int(parts[4])
                        
                        total = user + nice + system + idle
                        total_idle = idle
                        
                        # Calculate individual core load
                        if cpu_name in self.prev_cpu_stats:
                            prev_total, prev_idle = self.prev_cpu_stats[cpu_name]
                            total_diff = total - prev_total
                            idle_diff = total_idle - prev_idle
                            
                            if total_diff != 0:
                                core_load = 100.0 * (total_diff - idle_diff) / total_diff
                                self.cpu_loads[i] = round(core_load, 0)
                        
                        self.prev_cpu_stats[cpu_name] = (total, total_idle)
                        
        except Exception as e:
            # If we can't get detailed CPU loads, keep existing values
            pass

    def get_gpu_info(self):
        """Get GPU information using nvidia-smi if available."""
        try:
            # Try to get NVIDIA GPU info
            result = subprocess.run(['nvidia-smi', 
                                   '--query-gpu=temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.gr,clocks.mem',
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse nvidia-smi output
                output = result.stdout.strip()
                if output:
                    parts = output.split(', ')
                    if len(parts) >= 7:
                        self.gpu_temp = float(parts[0])  # Temperature
                        self.gpu_load = float(parts[1])  # GPU utilization
                        vram_percentage = float(parts[2])  # Memory utilization
                        self.gpu_vram_used = float(parts[3])  # Memory used
                        self.gpu_vram_total = float(parts[4])  # Memory total
                        self.gpu_core_clock = int(float(parts[5]))  # Graphics clock (as integer)
                        self.gpu_mem_clock = int(float(parts[6]))  # Memory clock (as integer)
                        
                        # Calculate VRAM percentage
                        if self.gpu_vram_total > 0:
                            self.gpu_vram_percentage = int((self.gpu_vram_used * 100) / self.gpu_vram_total)
            else:
                # If nvidia-smi is not available, try other methods
                # For AMD GPUs, we could use rocm-smi or other tools
                pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # nvidia-smi not available, GPU info will remain at defaults
            pass
        except Exception:
            pass


    def get_system_info(self):
        """Get overall system information."""
        self.get_cpu_info()
        self.get_gpu_info()
        self.get_cpu_loads()

    def get_formatted_data(self):
        """Format data in the same way as the C# application."""
        # Format data in the same way as the C# application
        # Format: cpuload0a+cpuload1b+...+cpuload15q+fps1r+tempCPUs+tempGPUt+cpuLoadu+ghzAvgv+gpuClkw+memClkx+gpuLoady+vram%z
        data = (
            f"{self.cpu_loads[0]}a{self.cpu_loads[1]}b{self.cpu_loads[2]}c{self.cpu_loads[3]}d"
            f"{self.cpu_loads[4]}e{self.cpu_loads[5]}f{self.cpu_loads[6]}g{self.cpu_loads[7]}h"
            f"{self.cpu_loads[8]}k{self.cpu_loads[9]}j{self.cpu_loads[10]}l{self.cpu_loads[11]}m"
            f"{self.cpu_loads[12]}n{self.cpu_loads[13]}o{self.cpu_loads[14]}p{self.cpu_loads[15]}q"
            f"{self.fps}r{self.cpu_package_temp:.0f}s{self.gpu_temp:.0f}t{self.cpu_total_load}u"
            f"{self.ghz_avg:.1f}v{self.gpu_core_clock}w{self.gpu_mem_clock}x{self.gpu_load:.0f}y{self.gpu_vram_percentage}z"
        )
        return data


class ArduinoCommunicator:
    def __init__(self, port_name=None, baud_rate=9600):
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.serial_port = None
        self.monitor = HardwareMonitor()
        
    def find_arduino_port(self):
        """Try to find the Arduino port automatically."""
        import glob
        # Common Arduino port patterns on Linux
        possible_ports = []
        possible_ports.extend(glob.glob('/dev/ttyUSB*'))  # USB serial
        possible_ports.extend(glob.glob('/dev/ttyACM*'))  # Arduino CDC ACM
        
        # If a specific port was provided, use it
        if self.port_name:
            return self.port_name
            
        # Otherwise try to find an available port
        for port in possible_ports:
            try:
                with serial.Serial(port, self.baud_rate, timeout=1) as test_port:
                    return port
            except serial.SerialException:
                continue
        
        # If no port found, return the first one (will fail when trying to connect)
        return possible_ports[0] if possible_ports else '/dev/ttyUSB0'

    def connect(self):
        """Connect to the Arduino."""
        try:
            port = self.find_arduino_port()
            self.serial_port = serial.Serial(port, self.baud_rate, timeout=1)
            print(f"Connected to Arduino on {port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False

    def disconnect(self):
        """Disconnect from the Arduino."""
        if self.serial_port and self.serial_port.is_open:
            try:
                # Send disconnect signal as in the original C# code
                self.serial_port.write(b"DISa")
            except:
                pass  # Ignore errors when disconnecting
            self.serial_port.close()
            print("Disconnected from Arduino")

    def send_data(self):
        """Send hardware data to Arduino."""
        if not self.serial_port or not self.serial_port.is_open:
            return False
            
        try:
            self.monitor.get_system_info()
            data = self.monitor.get_formatted_data()
            self.serial_port.write(data.encode())
            return True
        except serial.SerialException as e:
            print(f"Error sending data: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def run(self, interval=1000):
        """Main loop to continuously send data."""
        if not self.connect():
            return
            
        print("Starting hardware monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while self.monitor.running:
                if not self.send_data():
                    print("Failed to send data, attempting to reconnect...")
                    time.sleep(1)
                    if not self.connect():
                        time.sleep(5)  # Wait longer before retrying
                        continue
                
                time.sleep(interval / 1000.0)  # Convert milliseconds to seconds
        except KeyboardInterrupt:
            print("\nStopping hardware monitoring...")
        finally:
            self.disconnect()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hardware Monitor for Arduino on Linux')
    parser.add_argument('--port', '-p', help='Serial port for Arduino (e.g., /dev/ttyUSB0 or /dev/ttyACM0)')
    parser.add_argument('--baud', '-b', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--interval', '-i', type=int, default=1000, help='Update interval in milliseconds (default: 1000)')
    
    args = parser.parse_args()
    
    communicator = ArduinoCommunicator(port_name=args.port, baud_rate=args.baud)
    communicator.run(interval=args.interval)


if __name__ == "__main__":
    main()
