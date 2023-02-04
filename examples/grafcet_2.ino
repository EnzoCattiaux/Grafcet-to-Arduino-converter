/*
	Codice generato con convertitore grafcet -> arduino
	programmato con python da Enzo Cattiaux
	versione programma 2.0 (03.02.2023)
	04 February 2023 13:28:13
*/

//Inserire i pin dei componenti
const int pin_START = ;
const int pin_a1 = ;
const int pin_a0 = ;
const int pin_HL1 = ;
const int pin_A = ;

bool START, a1, a0, HL1, A;
int stato, oldStato;
unsigned long T=millis();
const int S1 = 0, S2 = 1, S3 = 2, S4 = 3;

void setup(){
	pinMode(pin_START, INPUT);
	pinMode(pin_a1, INPUT);
	pinMode(pin_a0, INPUT);
	pinMode(pin_HL1, OUTPUT);
	pinMode(pin_A, OUTPUT);

	stato = ;	//inserire lo stato iniziale
	oldStato = stato;
}

void loop(){
	START = digitalRead(pin_START);
	a1 = digitalRead(pin_a1);
	a0 = digitalRead(pin_a0);

	switch(stato){
		case S1:
			if(START) stato = S2;
			break;
		case S2:
			if(a1) stato = S3;
			break;
		case S3:
			if(millis()-T>5*1000) stato = S4;
			break;
		case S4:
			if(a0) stato = S0;
			break;
	}

	if(stato == S1){
		HL1 = HIGH;
	}
	if(stato == S2){
		A = HIGH;
	}
	if(stato == S3){
		A = HIGH;
	}

	if(oldStato != stato){
		T = millis();
		HL1 = LOW;
		A = LOW;
		A = LOW;
		oldStato = stato;
	}

	digitalWrite(pin_HL1, HL1);
	digitalWrite(pin_A, A);
}