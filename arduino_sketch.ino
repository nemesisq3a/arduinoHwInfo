#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);
String inData;
bool disconnected;

//0% custom character
byte zero[8] = {
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
};
//14% custom character
byte fourteen[8] = {
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
  B11111,
};
//28% custom character
byte twentyeight[8] = {
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
  B11111,
  B11111,
};
//42% custom character
byte fortytwo[8] = {
  B00000,
  B00000,
  B00000,
  B00000,
  B11111,
  B11111,
  B11111,
};
//57% custom character
byte fiftyuseven[8] = {
  B00000,
  B00000,
  B00000,
  B11111,
  B11111,
  B11111,
  B11111,
};
//71% custom character
byte seventyone[8] = {
  B00000,
  B00000,
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
};
//85% custom character
byte eightyfive[8] = {
  B00000,
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
};
//100% custom character
byte onehundred[8] = {
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
  B11111,
};

//Print loadbar function
void printCharacter(int x){
  inData.remove(inData.length() - 1, 1);
  lcd.setCursor(x,3);
  if (inData.toInt() == 0) lcd.write(byte(0));
  else if (inData.toInt() < 14) lcd.write(byte(1));
  else if (inData.toInt() < 28) lcd.write(byte(2));
  else if (inData.toInt() < 42) lcd.write(byte(3));
  else if (inData.toInt() < 57) lcd.write(byte(4));
  else if (inData.toInt() < 71) lcd.write(byte(5));
  else if (inData.toInt() < 85) lcd.write(byte(6));
  else if (inData.toInt() <= 100) lcd.write(byte(7));
  inData = "";
}

//Reset Screen Function
void clearScreen(){
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("GPU: 00 C VM  FPS   ");
  lcd.setCursor(7,0);
  lcd.print((char)223);
  lcd.setCursor(0,1);
  lcd.print("0000Mhz/0000Mhz 000%");
  lcd.setCursor(0,2);
  lcd.print("CPU: 00 C 0,0Gz 000%");
  lcd.setCursor(7,2);
  lcd.print((char)223);
  lcd.setCursor(1,3);
  lcd.print("[");
  lcd.setCursor(18,3);
  lcd.print("]");
}

//Main Function
void setup() {
  lcd.begin(20,4);
  lcd.backlight();
  //lcd.setBacklight(20);
  lcd.createChar(0, zero);
  lcd.createChar(1, fourteen);
  lcd.createChar(2, twentyeight);
  lcd.createChar(3, fortytwo);
  lcd.createChar(4, fiftyuseven);
  lcd.createChar(5, seventyone);
  lcd.createChar(6, eightyfive);
  lcd.createChar(7, onehundred);
  Serial.begin(9600);
  clearScreen();
}

//Main Loop
void loop() {
    while (Serial.available() > 0)
    {
      char recieved = Serial.read();
      inData += recieved;

      if (recieved == 'a')
        {
            //Cpu Load Graph
            inData.remove(inData.length() - 1, 1);
            lcd.setCursor(2,3);
            if (inData.toInt() == 0) lcd.write(byte(0));
            else if (inData.toInt() < 14) lcd.write(byte(1));
            else if (inData.toInt() < 28) lcd.write(byte(2));
            else if (inData.toInt() < 42) lcd.write(byte(3));
            else if (inData.toInt() < 57) lcd.write(byte(4));
            else if (inData.toInt() < 71) lcd.write(byte(5));
            else if (inData.toInt() < 85) lcd.write(byte(6));
            else if (inData.toInt() <= 100) lcd.write(byte(7));

            // IF DIS Clear screen and reset data
            if(inData == "DIS")
            {
              clearScreen();
            }

            inData = "";
        }

        //Switch Case for Per Core load
        switch (recieved) {
          case 'b':
            printCharacter(3);
            break;
          case 'c':
            printCharacter(4);
            break;
          case 'd':
            printCharacter(5);
            break;
          case 'e':
            printCharacter(6);
            break;
          case 'f':
            printCharacter(7);
            break;
          case 'g':
            printCharacter(8);
            break;
          case 'h':
            printCharacter(9);
            break;
          case 'k':
            printCharacter(10);
            break;
          case 'j':
            printCharacter(11);
            break;
          case 'l':
            printCharacter(12);
            break;
          case 'm':
            printCharacter(13);
            break;
          case 'n':
            printCharacter(14);
            break;
          case 'o':
            printCharacter(15);
            break;
          case 'p':
            printCharacter(16);
            break;
          case 'q':
            printCharacter(17);
            break;
     }

     //FPS Counter from RivaTuner
     if (recieved == 'r')
        {
            inData.remove(inData.length() - 1, 1);
            int gpuFpsLenght = inData.length();
            lcd.setCursor(17,0);
            switch (gpuFpsLenght) {
              case 1:
                lcd.print("  ");
                lcd.print(inData);
                inData = "";
                break;
              case 2:
                lcd.print(" ");
                lcd.print(inData);
                inData = "";
                break;
              case 3:
                lcd.print(inData);
                inData = "";
                break;
           }
        }

     //CPU Temp
     if (recieved == 's')
        {
            inData.remove(inData.length() - 1, 1);
            lcd.setCursor(5,2);
            lcd.print(inData);         
            inData = "";
        }
        
     //GPU Temp
     if (recieved == 't')
        {
            inData.remove(inData.length() - 1, 1);
            lcd.setCursor(5,0);
            lcd.print(inData + (char)223 + 'C ');          
            inData = "";
        }

     //CPU Load
     if (recieved == 'u')
        {
            inData.remove(inData.length() - 1, 1);
            int cpuLoadLenght = inData.length();
            lcd.setCursor(16,2);
            switch (cpuLoadLenght) {
              case 1:
                lcd.print("  ");
                lcd.print(inData);
                inData = "";
                break;
              case 2:
                lcd.print(" ");
                lcd.print(inData);
                inData = "";
                break;
              case 3:
                lcd.print(inData);
                inData = "";
                break;
              }
        }
        
      //CPU Average Frequency
      if (recieved == 'v')
        {
            inData.remove(inData.length() - 1, 1);
            lcd.setCursor(10,2);
            lcd.print(inData);            
            inData = "";
        }
        
      //GPU Core Frequency
      if (recieved == 'w')
        {
            inData.remove(inData.length() - 1, 1);
            if (inData.length() == 3){
              lcd.setCursor(0,1);
              lcd.print(" ");
            }
            else
            {
              lcd.setCursor(0,1);
            }
            lcd.print(inData);
            inData = "";
        }

      //GPU Memory Frequency
      if (recieved == 'x')
        {
            inData.remove(inData.length() - 1, 1);
            if (inData.length() == 3){
              lcd.setCursor(8,1);
              lcd.print(" ");
            }
            else
            {
              lcd.setCursor(8,1);
            }
            lcd.print(inData);
            inData = "";
        }

     //GPU Load
     if (recieved == 'y')
        {
            inData.remove(inData.length() - 1, 1);
            int gpuLoadLenght = inData.length();
            lcd.setCursor(16,1);
            switch (gpuLoadLenght) {
              case 1:
                lcd.print("  ");
                lcd.print(inData);
                inData = "";
                break;
              case 2:
                lcd.print(" ");
                lcd.print(inData);
                inData = "";
                break;
              case 3:
                lcd.print(inData);
                inData = "";
                break;
              }
        }

     //GPU Video Memory Usage Percentage   
     if (recieved == 'z')
        {
          inData.remove(inData.length() - 1, 1);
          lcd.setCursor(12,0);
          if (inData.toInt() == 0) lcd.write(byte(0));
          else if (inData.toInt() < 14) lcd.write(byte(1));
          else if (inData.toInt() < 28) lcd.write(byte(2));
          else if (inData.toInt() < 42) lcd.write(byte(3));
          else if (inData.toInt() < 57) lcd.write(byte(4));
          else if (inData.toInt() < 71) lcd.write(byte(5));
          else if (inData.toInt() < 85) lcd.write(byte(6));
          else if (inData.toInt() <= 100) lcd.write(byte(7));
          inData = "";
        }
    }
}
