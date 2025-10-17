#!/usr/bin/env python3
"""
Test script to check CPU temperature reading methods
"""

import subprocess
import re
from pathlib import Path

def get_cpu_temperature_sensors():
    """Get CPU temperature using the 'sensors' command from lm-sensors."""
    try:
        # Run 'sensors' command to get hardware temperatures
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        output = result.stdout
        print("Sensors output:")
        print(output)
        
        # Prioritize specific sensors, especially Tctl for AMD CPUs
        # Look for Tctl first as it's the requested temperature
        tctl_match = re.search(r'Tctl:.*\+([0-9]+\.[0-9]+)', output)
        if tctl_match:
            temp = float(tctl_match.group(1))
            print(f"Found Tctl temperature: {temp}°C")
            return temp
        
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
                print(f"Found temperatures with pattern '{pattern}': {temps}")
        
        if all_temps:
            # Return the highest temperature found from remaining sensors
            max_temp = max(all_temps)
            print(f"Maximum temperature from other sensors: {max_temp}°C")
            return max_temp
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 'sensors' command not available or failed
        print("'sensors' command not available or failed")
        pass
    except Exception as e:
        print(f"Error running sensors: {e}")
        pass
    
    return None

def get_cpu_temperature_thermal_zones():
    """Get CPU temperature from thermal zones in /sys/class/thermal/."""
    try:
        cpu_temp = 0
        print("Checking thermal zones...")
        for i in range(20):  # Check first 20 thermal zones
            temp_path = f"/sys/class/thermal/thermal_zone{i}/temp"
            type_path = f"/sys/class/thermal/thermal_zone{i}/type"
            
            if Path(temp_path).exists() and Path(type_path).exists():
                with open(type_path, 'r') as f:
                    type_name = f.read().strip()
                
                print(f"Thermal zone {i}: {type_name}")
                
                # Check for CPU-related thermal zones
                if any(keyword in type_name.lower() for keyword in ['cpu', 'package', 'core']):
                    with open(temp_path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0  # Convert from millidegrees
                        cpu_temp = max(cpu_temp, temp)
                        print(f"  -> CPU-related zone found: {temp}°C")
        
        return cpu_temp if cpu_temp > 0 else None
    except Exception as e:
        print(f"Error reading thermal zones: {e}")
        return None

def main():
    print("Testing CPU temperature reading methods...\n")
    
    print("Method 1: Using 'sensors' command")
    temp1 = get_cpu_temperature_sensors()
    print(f"Result: {temp1}°C\n")
    
    print("Method 2: Using thermal zones")
    temp2 = get_cpu_temperature_thermal_zones()
    print(f"Result: {temp2}°C\n")
    
    if temp1 is not None:
        print(f"Temperature from sensors: {temp1}°C")
    elif temp2 is not None:
        print(f"Temperature from thermal zones: {temp2}°C")
    else:
        print("Could not read CPU temperature with either method")
        print("\nMake sure lm-sensors is installed and configured:")
        print("  sudo apt install lm-sensors")
        print(" sudo sensors-detect")

if __name__ == "__main__":
    main()
