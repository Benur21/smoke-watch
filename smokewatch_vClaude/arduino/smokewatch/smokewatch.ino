// SmokeWatch — Arduino
// Envia "AO,DO\n" a cada segundo via porta série.
// LED pino 13 espelha o valor DO do sensor FC-22.

const int AO_PIN  = A0;  // saída analógica do FC-22
const int DO_PIN  = 2;   // saída digital do FC-22
const int LED_PIN = 13;  // LED built-in

void setup() {
  Serial.begin(9600);
  pinMode(DO_PIN,  INPUT);
  pinMode(LED_PIN, OUTPUT);
  // Aquecimento do sensor: 20 segundos com LED a piscar
  for (int i = 0; i < 20; i++) {
    digitalWrite(LED_PIN, HIGH); delay(500);
    digitalWrite(LED_PIN, LOW);  delay(500);
  }
}

void loop() {
  int ao    = analogRead(AO_PIN);
  int doVal = digitalRead(DO_PIN);  // 0 ou 1

  // LED espelha DO
  digitalWrite(LED_PIN, doVal == HIGH ? HIGH : LOW);

  // Envia para o Pi
  Serial.print(ao);
  Serial.print(',');
  Serial.println(doVal);

  delay(1000);
}
