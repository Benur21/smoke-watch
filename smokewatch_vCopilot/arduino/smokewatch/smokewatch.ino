const uint8_t ANALOG_PIN = A0;
const uint8_t DIGITAL_PIN = 2;
const uint8_t LED_PIN = 13;

void setup() {
  pinMode(ANALOG_PIN, INPUT);
  pinMode(DIGITAL_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int aoValue = analogRead(ANALOG_PIN);
  int doValue = digitalRead(DIGITAL_PIN);

  digitalWrite(LED_PIN, doValue ? LOW : HIGH);

  Serial.print(aoValue);
  Serial.print(',');
  Serial.println(doValue);

  delay(1000);
}
