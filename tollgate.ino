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
  Serial.println("Tap E-Toll...");
  Serial.println();
  digitalWrite(LED_R, HIGH);

}

void palang(int dari, int ke, int jeda) {
  if (dari < ke) {
    for (int i = dari; i <= ke; i++) {
      myServo.write(i);
      delay(jeda);
    }
  } else {
    for (int i = dari; i >= ke; i--) {
      myServo.write(i);
      delay(jeda);
    }
  }
}

void loop() 
{
  mfrc522.PCD_StopCrypto1();

  if ( ! mfrc522.PICC_IsNewCardPresent()) 
  {
    return;
  }
  
  if ( ! mfrc522.PICC_ReadCardSerial()) 
  {
    mfrc522.PCD_Init();
    return;
  }
  
  Serial.print("E-Toll :");
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
  Serial.print("Pesan : ");
  content.toUpperCase();
  if (content.substring(1) == "D3 3E 2C DD") //UID
  {
    Serial.println("Tap E-Toll Berhasil");
    Serial.println();
    delay(500);
    tone(BUZZER, 2500);
    delay(150);
    noTone(BUZZER);
    digitalWrite(LED_G, HIGH);
    digitalWrite(LED_R, LOW);
    palang(6, 103, 4);
    delay(5000);
    palang(103, 6, 4);
    digitalWrite(LED_G, LOW);
    digitalWrite(LED_R, HIGH);
  }
 
 else   {
    Serial.println("Tap E-Toll Gagal");
    tone(BUZZER, 2500);
    delay(500);
    noTone(BUZZER);
  }
}
