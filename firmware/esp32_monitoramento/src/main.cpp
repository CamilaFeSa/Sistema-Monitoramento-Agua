#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 inicializado com sucesso para o TCC!");
}

void loop() {
  Serial.println("Sistema rodando...");
  delay(2000);
}