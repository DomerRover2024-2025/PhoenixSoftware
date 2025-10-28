/*
 * Arduino sketch for 3x SmartDriveDuo-30 motor controllers
 * Controls 3 left wheels and 3 right wheels (grouped)
 * Receives two space-separated values over serial: "left right\n"
 * Each value is applied to all left or all right wheels.
 */

// Left wheels: FL, BL, ML
const int FL_PWM_PIN = 10; 
const int FL_DIR_PIN = 8;   // Motor controller 1
const int BL_PWM_PIN = 24;  
const int BL_DIR_PIN = 2;   // Motor controller 2
const int ML_PWM_PIN = 13; 
const int ML_DIR_PIN = 6;   // Motor controller 3

// Right wheels: FR, MR, RB
const int FR_PWM_PIN = 5;  
const int FR_DIR_PIN = 3;   // Motor controller 2
const int MR_PWM_PIN = 7;  
const int MR_DIR_PIN = 4;   // Motor controller 3
const int RB_PWM_PIN = 11; 
const int RB_DIR_PIN = 12;  // Motor controller 1

void setup() {
  Serial.begin(115200);
  pinMode(FL_PWM_PIN, OUTPUT); pinMode(FL_DIR_PIN, OUTPUT);
  pinMode(BL_PWM_PIN, OUTPUT); pinMode(BL_DIR_PIN, OUTPUT);
  pinMode(ML_PWM_PIN, OUTPUT); pinMode(ML_DIR_PIN, OUTPUT);
  pinMode(FR_PWM_PIN, OUTPUT); pinMode(FR_DIR_PIN, OUTPUT);
  pinMode(MR_PWM_PIN, OUTPUT); pinMode(MR_DIR_PIN, OUTPUT);
  pinMode(RB_PWM_PIN, OUTPUT); pinMode(RB_DIR_PIN, OUTPUT);
}

void setMotor(int speed, int pwmPin, int dirPin) {
  int pwm = abs(speed);
  bool direction = (speed >= 0); // HIGH for forward, LOW for reverse
  analogWrite(pwmPin, pwm);
  digitalWrite(dirPin, direction ? HIGH : LOW);
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    int sep = line.indexOf(' ');
    if (sep > 0) {
      int left = line.substring(0, sep).toInt();
      int right = line.substring(sep + 1).toInt();
      left = constrain(left, -255, 255);
      right = constrain(right, -255, 255);

      // Apply the same instruction to all three left wheels
      setMotor(left, FL_PWM_PIN, FL_DIR_PIN);
      setMotor(left, BL_PWM_PIN, BL_DIR_PIN);
      setMotor(left, ML_PWM_PIN, ML_DIR_PIN);

      // Apply the same instruction to all three right wheels
      setMotor(right, FR_PWM_PIN, FR_DIR_PIN);
      setMotor(right, MR_PWM_PIN, MR_DIR_PIN);
      setMotor(right, RB_PWM_PIN, RB_DIR_PIN);
    }
  }
}
