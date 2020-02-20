using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.IO.Ports;
using LibreHardwareMonitor.Hardware;
using RTSSSharedMemoryNET;

namespace ArduinoHwInfo
{
    public partial class Form1 : Form
    {
        //Libre Hardware Monitor declaration for CPU and GPU only
        Computer c = new Computer()
        {
            IsGpuEnabled = true,
            IsCpuEnabled = true,
        };

        //Variables and arrays declaration
        double value1, value3, value4, value5, value7, value8;
        float value2, value6;
        int[] cpuloadvalue = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
        int[] cpumhzvalue = { 0, 0, 0, 0, 0, 0, 0, 0 };
        int fps1;

        //New serial port
        private SerialPort port = new SerialPort();
        
        //Form Main process
        public Form1()
        {
            InitializeComponent();
            Init();
            c.Open();
            Start();
        }

        //Form Inizialization
        private void Init()
        {
            try
            {
                notifyIcon1.Visible = false;
                port.Parity = Parity.None;
                port.StopBits = StopBits.One;
                port.DataBits = 8;
                port.Handshake = Handshake.None;
                port.RtsEnable = true;
                string[] ports = SerialPort.GetPortNames();
                foreach (string port in ports)
                {
                    comboBox1.Items.Add(port);
                }
                port.BaudRate = 9600;
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        //Start Minitoring
        private void button1_Click(object sender, EventArgs e)
        {
            Start();
        }

        //Minimize form
        private void Form1_Resize(object sender, EventArgs e)
        {
            if (this.WindowState == FormWindowState.Minimized)
            {
                Hide();
                notifyIcon1.Visible = true;
            }
        }

        //Restore form 1
        private void notifyIcon1_MouseDoubleClick_1(object sender, MouseEventArgs e)
        {
                Show();
                this.WindowState = FormWindowState.Normal;
                notifyIcon1.Visible = false;
        }

        //Stop Monitoring
        private void button2_Click_1(object sender, EventArgs e)
        {
            try
            {
                port.Write("DISa");
                port.Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
            toolStripStatusLabel1.Text = "Disconnesso";
            timer1.Enabled = false;
        }

        //Restore Form
        private void NotifyIcon1_MouseDoubleClick(object sender, MouseEventArgs e)
        {

            this.notifyIcon1.Visible = true;
            this.WindowState = FormWindowState.Normal;
        }

        //Timer Execution
        private void timer1_Tick(object sender, EventArgs e)
        {
            Status();
        }

        //Serial selection and start monitoring
        private void Start()
        {
            try
            {
                if (!port.IsOpen)
                {
                    port.PortName = comboBox1.Text;
                    port.Open();
                    timer1.Interval = Convert.ToInt32(comboBox2.Text);
                    timer1.Enabled = true;
                    timer1.Tick += new EventHandler(timer1_Tick);
                    toolStripStatusLabel1.Text = "Connesso";
                    notifyIcon1.BalloonTipText = "Connesso";
                    notifyIcon1.ShowBalloonTip(5);
                }

            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        //Monitoring Function
        private void Status()
        {
            foreach (var hardware in c.Hardware)
            {
                //TEST GPU
                if (hardware.HardwareType == HardwareType.GpuNvidia)
                {
                    hardware.Update();
                    foreach (var sensor in hardware.Sensors)
                    {
                        if (sensor.SensorType == SensorType.Temperature && sensor.Name.Contains("GPU Core"))
                        {
                            value2 = sensor.Value.GetValueOrDefault();
                        }
                        if (sensor.SensorType == SensorType.Clock && sensor.Name.Contains("GPU Core"))
                        {
                            value3 = Math.Round(sensor.Value.GetValueOrDefault(), 0);
                        }
                        if (sensor.SensorType == SensorType.Clock && sensor.Name.Contains("GPU Memory"))
                        {
                            value5 = Math.Round(sensor.Value.GetValueOrDefault(), 0);
                        }
                        if (sensor.SensorType == SensorType.Load && sensor.Name.Contains("GPU Core"))
                        {
                            value6 = sensor.Value.GetValueOrDefault();
                        }
                        if (sensor.SensorType == SensorType.SmallData && sensor.Name.Contains("GPU Memory Total"))
                        {
                            value7 = sensor.Value.GetValueOrDefault();
                        }
                        if (sensor.SensorType == SensorType.SmallData && sensor.Name.Contains("GPU Memory Used"))
                        {
                            value8 = sensor.Value.GetValueOrDefault();
                        }
                    }

                }

                //TEST CPU
                if (hardware.HardwareType == HardwareType.Cpu)
                {
                    hardware.Update();
                    foreach (var sensor in hardware.Sensors) { 
                        for (int i = 0; i < 16; i++)
                            {
                            if (sensor.SensorType == SensorType.Load && sensor.Name.Equals("CPU Core #" + (i+1)))
                            {
                                cpuloadvalue[i] = (int)Math.Round(sensor.Value.GetValueOrDefault(), 0);
                            }
                            if (sensor.SensorType == SensorType.Clock && sensor.Name.Equals("Core #" + (i+1)))
                            {
                                cpumhzvalue[i]  = (int)Math.Round(sensor.Value.GetValueOrDefault(), 0);
                            }
                        }
                        if (sensor.SensorType == SensorType.Temperature && sensor.Name.Contains("Core (Tctl/Tdie)"))
                        {
                            value1 = Math.Round(sensor.Value.GetValueOrDefault(), 0);
                        }
                        if (sensor.SensorType == SensorType.Load && sensor.Name.Contains("CPU Total"))
                        {
                            value4 = Math.Round(sensor.Value.GetValueOrDefault(), 0);
                        }
                    }
                }

                //Average Ghz Core
                double mhzSum = cpumhzvalue.Average()/1000;
                double ghzAvg = Math.Round(mhzSum, 1);
                
                //VRAM Usage %
                int vramPercentage = (int)(value8*100/value7);

                //RivaTuner Shared Memory Inizialization
                var appEntries = OSD.GetAppEntries().Where(x => (x.Flags & AppFlags.MASK) != AppFlags.None).ToArray();
                
                fps1 = 0;
                
                foreach (var app in appEntries)
                {
                    if (app.InstantaneousFrames != 0)
                    {
                        fps1 = checked((int)app.InstantaneousFrames);
                    }
                }
                try
                {
                    port.Write(cpuloadvalue[0] + "a" + cpuloadvalue[1] + "b" + cpuloadvalue[2] + "c" + cpuloadvalue[3] + "d" + cpuloadvalue[4] + "e" + cpuloadvalue[5] + "f" + cpuloadvalue[6] + "g" + cpuloadvalue[7] + "h" + cpuloadvalue[8] + "k" + cpuloadvalue[9] + "j" + cpuloadvalue[10] + "l" + cpuloadvalue[11] + "m" + cpuloadvalue[12] + "n" + cpuloadvalue[13] + "o" + cpuloadvalue[14] + "p" + cpuloadvalue[15] + "q" + fps1 + "r" + value1 + "s" + value2 + "t" + value4 + "u" + ghzAvg.ToString() + "v" + value3 + "w" + value5 + "x" + value6 + "y" + vramPercentage + "z");
                }
                catch (Exception ex)
                {
                    timer1.Stop();
                    MessageBox.Show(ex.Message);
                }

            }
        }
    }
}
