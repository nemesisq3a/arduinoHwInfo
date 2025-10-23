# ArduinoHwInfo 
# Arduino Hardware Monitor for Windows
Arduino controlled hardware monitor for x64 Windows 11.
First implementation of arduino for CPU/GPU/FPS monitoring.
Feel free to use my code for you projects.
For the CPU/GPU information I used the https://github.com/LibreHardwareMonitor/LibreHardwareMonitor project.
For the FPS monitoring I used the https://github.com/spencerhakim/RTSSSharedMemoryNET solution to read FPS from Afterburner.
For both this projects you can find the x64 dll bundled inside the solution but feel free to build on your own.
My project is calibrated for a 16 cores, and a 20x4 i2c controller LCD display.
Remember to download MSI Afterburner an launch it before this program to obtain the FPS values, and **always run arduinoHWInfo with admin privileges**.

# Arduino Hardware Monitor for Linux
This Python program replicates the functionality of the Windows C# ArduinoHwInfo application on Linux. It collects hardware information (CPU/GPU temperatures, loads, frequencies) and sends it to an Arduino via serial communication using the same format as the original Windows application.

## Features

- Monitors CPU and GPU temperatures, loads, and frequencies
- Collects system information similar to the original C# application
- Sends data to Arduino using the same format as the Windows version
- Automatic Arduino port detection
- Configurable update interval

## Requirements

- Python 3.6 or higher
- `pyserial` library
- Linux system with hardware monitoring support (lm-sensors, nvidia-smi for NVIDIA GPUs)
- Arduino connected via USB

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install system dependencies for hardware monitoring:
   ```bash
   # For CPU temperature monitoring
   sudo apt install lm-sensors
   
   # For NVIDIA GPU monitoring (if applicable)
   sudo apt install nvidia-utils-XXX  # Replace XXX with your driver version
   ```

3. Run sensors detection (follow prompts):
   ```bash
   sudo sensors-detect
   ```

## Usage

```bash
python3 arduino_hw_info.py [options]
```

### Options

- `--port, -p`: Specify the serial port for Arduino (e.g., `/dev/ttyUSB0` or `/dev/ttyACM0`). If not specified, the program will try to auto-detect the Arduino port.
- `--baud, -b`: Set the baud rate (default: 9600)
- `--interval, -i`: Set the update interval in milliseconds (default: 1000)

### Examples

```bash
# Auto-detect Arduino port with default settings
python3 arduino_hw_info.py

# Specify Arduino port and update interval
python3 arduino_hw_info.py --port /dev/ttyUSB0 --interval 500

# Use different baud rate
python3 arduino_hw_info.py --baud 115200
```

## Data Format

The program sends data to the Arduino using the same format as the original C# application:

`cpuload0a+cpuload1b+...+cpuload15q+fps1r+tempCPUs+tempGPUt+cpuLoadu+ghzAvgv+gpuClkw+memClkx+gpuLoady+vram%z`

This ensures that the Arduino sketch remains unchanged and works the same way as with the Windows application.

## Compatibility

- The program is designed to work with the same Arduino sketch used by the original Windows application
- Supports NVIDIA GPU monitoring via `nvidia-smi`
- CPU monitoring via `/proc` and `/sys` filesystems
- Automatic detection of Arduino on common Linux serial ports

## Troubleshooting

### Permission Issues

If you encounter permission issues accessing the serial port, add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in for the changes to take effect.

### No Hardware Data

If hardware data is not being collected:
- Ensure `lm-sensors` is properly configured: run `sensors` command to verify
- For NVIDIA GPUs, ensure `nvidia-smi` works from the command line
- Check that your system supports the required monitoring interfaces

## Auto-start on Boot

To automatically start the hardware monitor after user login, you have two options:

### Option 1: Desktop Autostart (User Session)

1. First, update the path in the `arduino_hw_info.desktop` file to match your actual user directory:
   - Edit the file and change `/home/nemesisq3a/` to your actual home directory path
   - The Exec line should point to the correct location of `arduino_hw_info.py`

2. Copy the updated `arduino_hw_info.desktop` file to your autostart directory:
   ```bash
   mkdir -p ~/.config/autostart
   cp arduino_hw_info.desktop ~/.config/autostart/
   ```

### Option 2: Systemd Service (System Level)

1. Install the required Python dependencies system-wide:
   ```bash
   sudo pip install pyserial
   ```

2. First, update the paths in the `arduino-hw-monitor.service` file to match your actual user directory:
   - Edit the file and change `/home/nemesisq3a/` to your actual home directory path
   - Both ExecStart and WorkingDirectory should point to the correct location

3. Copy the updated service file to the systemd user directory:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp arduino-hw-monitor.service ~/.config/systemd/user/
   ```

4. Enable and start the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable arduino-hw-monitor.service
   systemctl --user start arduino-hw-monitor.service
   ```

5. To check if the service is running:
   ```bash
   systemctl --user status arduino-hw-monitor.service
   ```

6. To view service logs:
   ```bash
   journalctl --user -u arduino-hw-monitor.service -f
   ```

The systemd service option is more robust as it will restart the application if it crashes and can run even if the desktop environment fails to start properly.

**Note:** Make sure to update the paths in both the .desktop and .service files to match your actual installation directory before using either method.

**Troubleshooting:** If the service fails to start or doesn't restart after reboot, ensure that:
- The Python script path in the service file is correct
- The Arduino is connected when the service starts
- The required Python dependencies are installed
- The service file has the correct permissions

