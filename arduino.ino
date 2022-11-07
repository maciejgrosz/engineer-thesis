#define A_PHASE 2
#define B_PHASE 3
unsigned int flag_A = 1000; //Assign a value to the token bit
unsigned int flag_B = 0;
double t_sampling = 10; //czas próbkowania w mili-sekundach !!!!
/** * */
void setup() {
    pinMode(A_PHASE, INPUT_PULLUP);
    pinMode(B_PHASE, INPUT_PULLUP);
    Serial.begin(9600); //Serial Port Baudrate: 9600
    attachInterrupt(digitalPinToInterrupt( A_PHASE), interrupt, RISING);
}
void loop() {
    Serial.print(",");
    Serial.println(flag_A-flag_B);
    Serial.print(millis());
    delay(t_sampling);
}
void interrupt()
{
    char i;
    i = digitalRead(B_PHASE);
    if (i == 1)
    flag_A += 1;
    else
    flag_B += 1;
} 
