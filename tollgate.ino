#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
 
#define SS_PIN 10
#define RST_PIN 9
#define LED_G 5 //define green LED pin
#define LED_R 4 //define red LED
#define BUZZER 2 //buzzer pin
#define TRIG_PIN 7
#define ECHO_PIN 6
MFRC522 mfrc522(SS_PIN, RST_PIN);   
Servo myServo; 
 
void setup() 
{
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  myServo.attach(3);
  myServo.write(6);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_R, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  noTone(BUZZER);
  Serial.println("Tempelkan kartu E-Toll...");
  Serial.println();
  digitalWrite(LED_R, HIGH);

}
void loop() 
{

  if ( ! mfrc522.PICC_IsNewCardPresent()) 
  {
    return;
  }
  
  if ( ! mfrc522.PICC_ReadCardSerial()) 
  {
    return;
  }
  
  Serial.print("UID tag :");
  String content= "";
  byte letter;
  for (byte i = 0; i < mfrc522.uid.size; i++) 
  {
     Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
     Serial.print(mfrc522.uid.uidByte[i], HEX);
     content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
     content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  Serial.println();
  Serial.print("Message : ");
  content.toUpperCase();
  if (content.substring(1) == "D3 3E 2C DD") //UID
  {
    Serial.println("Saldo E-Toll Cukup");
    Serial.println();
    delay(500);
    digitalWrite(LED_G, HIGH);
    digitalWrite(LED_R, LOW);
    tone(BUZZER, 200);
    delay(150);
    noTone(BUZZER);
    myServo.write(103);
    delay(5000);
    myServo.write(6);
    digitalWrite(LED_G, LOW);
    digitalWrite(LED_R, HIGH);
  }
 
 else   {
    Serial.println("Saldo E-Toll Tidak Cukup");
    tone(BUZZER, 200);
    delay(1000);
    noTone(BUZZER);
  }
}
