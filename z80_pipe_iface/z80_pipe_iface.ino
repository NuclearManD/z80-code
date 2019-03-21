#include <Wire.h>    
 
#define eeprom_adr 0x50

#define rd A0
#define done A1
#define doDone PORTC|=2;delayMicroseconds(1);PORTC^=2
#define getRd (PINC&1)==1
#define en 2
#define rdIn (PIND>>3)|(PINB<<5)

void wrOut(byte b){
  DDRD |= 0xf8;
  DDRB |= 0x7;
  PORTD=(PORTD&0x7)|(b<<3);
  PORTB=(PORTB&0xf8)|(b>>5);
  DDRD &= 0x7;
  DDRB &= 0xf8;
}

#define adr0 A3
#define adr1 A2

#define READY_BIT 2
#define ERROR_BIT 4
#define PIPE_FLAG 1
#define AVAIL_BIT 2

#define CMD_READ_SECTOR  0x10
#define CMD_WRITE_SECTOR 0x20
#define CMD_SET_ADR      0x30


byte buffer[256];
unsigned int sectorAddress;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  pinMode(done, OUTPUT);
  pinMode(rd, INPUT);
  pinMode(adr0, INPUT);
  pinMode(adr1, INPUT);
  digitalWrite(done, LOW);
  //attachInterrupt(digitalPinToInterrupt(en), z80_isr, FALLING);
}

long inClockTimer = micros();
float inClockFreq;
long timer = 0;

byte status = 0;
byte cmd = 0;
byte devSel = 0;

void loop() {
  if(!digitalRead(en))z80_isr();
  if(cmd==1){
    // clear error bit/warm reset
    status&=~(ERROR_BIT);
    cmd=0;
  }
}

byte getStatus(){
  byte stat = status;
  if(devSel==0){
    // UART device
    stat|=PIPE_FLAG;
    if(Serial.available())stat|=AVAIL_BIT;
  }
  return stat;
}

byte dataPop(){
  if(devSel==0)return Serial.read();
  else{
    status|=ERROR_BIT;
    return 0xFF;
  }
}
void dataWr(byte d){
  if(devSel==0)Serial.write(d);
  else{
    status|=ERROR_BIT;
  }
}
void z80_isr() {
  noInterrupts();
  byte adr = 0;
  if(digitalRead(adr0))adr|=1;
  if(digitalRead(adr1))adr|=2;
  if(getRd){
    byte inval = rdIn;
    if(adr==0)devSel=inval;
    else if(adr==1)dataWr(inval);
    else if(adr==2)cmd = inval;
    else if(adr==3)status|=ERROR_BIT;
    /*
    Serial.print("WR@");
    Serial.print(adr);
    Serial.print(":");
    Serial.println(inval,HEX); //*/
  }else{
    //Serial.print("RD@");
    //Serial.println(adr);
    byte outval;
    if(adr==0)outval=getStatus();
    else if(adr==1)outval=dataPop();
    else if(adr==2)outval=cmd;
    else if(adr==3)outval=1; // device count
    wrOut(outval);
  }
  doDone;
  interrupts();
}
// 256 byte sector
void writeSector(){
  if(devSel==1){
    for(int i=0;i<256;i+=16){
      _writeEEPROM((sectorAddress<<8)|i,buffer+i);
    }
  }
}
// 256 byte sector
void readSector(){
  if(devSel==1){
    int devAdr = (eeprom_adr|((sectorAddress>>6)&0x0E));
   
    Wire.beginTransmission(devAdr);
    Wire.write(sectorAddress&127);   // MSB
    Wire.write((sectorAddress<<8)&255); // LSB
    Wire.endTransmission();
   
    Wire.requestFrom(devAdr,16);
    for(int i=0;i<256;i++){
      if (Wire.available()) buffer[i] = Wire.read();
    }
  }
}
// 16 byte chunks
void _writeEEPROM(unsigned long adr, byte* data){
  int i=0;
  
  Wire.beginTransmission((int)(eeprom_adr|((adr>>14)&0x0E)));
  Wire.write((int)((adr >> 8)&127));   // MSB
  Wire.write((int)(adr & 0xFF)); // LSB

  for(int i=0;i<16;i++){
    Wire.write(data[i]);
  }
  Wire.endTransmission();
 
  delay(5);
}
// 16 byte chunks
byte* _readEEPROM(unsigned long adr, byte* buffer){
  int devAdr = (int)(eeprom_adr|((adr>>14)&0x0E));
 
  Wire.beginTransmission(devAdr);
  Wire.write((int)((adr >> 8)&127));   // MSB
  Wire.write((int)(adr & 0xFF)); // LSB
  Wire.endTransmission();
 
  Wire.requestFrom(devAdr,16);
  for(int i=0;i<16;i++){
    if (Wire.available()) buffer[i] = Wire.read();
  }
  return buffer;
}
