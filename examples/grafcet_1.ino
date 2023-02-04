/*
	Codice generato con convertitore grafcet -> arduino
	programmato con python da Enzo Cattiaux
	versione programma 2.0 (03.02.2023)
	04 February 2023 13:17:05
*/

//Inserire i pin dei componenti
const int pin_EN = ;
const int pin_F1 = ;
const int pin_F2 = ;
const int pin_P = ;
const int pin_HL1 = ;
const int pin_K1 = ;
const int pin_HAL = ;

bool EN, F1, F2, P, HL1, K1, HAL;
int stato, oldStato;
unsigned long T=millis();
const int S1 = 0, S2 = 1, S3 = 2, S4 = 3, S5 = 4;

void setup(){
	pinMode(pin_EN, INPUT);
	pinMode(pin_F1, INPUT);
	pinMode(pin_F2, INPUT);
	pinMode(pin_P, INPUT);
	pinMode(pin_HL1, OUTPUT);
	pinMode(pin_K1, OUTPUT);
	pinMode(pin_HAL, OUTPUT);

	stato = ;	//inserire lo stato iniziale
	oldStato = stato;
}

void loop(){
	EN = digitalRead(pin_EN);
	F1 = digitalRead(pin_F1);
	F2 = digitalRead(pin_F2);
	P = digitalRead(pin_P);

	switch(stato){
		case S1:
			if(EN) stato = S2;
			break;
		case S2:
			if(!EN) stato = S1;
			if((!F1 || !F2 || !P) && (millis()-T>5*1000)) stato = S3;
			break;
		case S3:
			if(!EN) stato = S1;
			if(millis()-T<5) stato = S4;
			break;
		case S4:
			if(!EN) stato = S1;
			if(millis()-T>10*1000) stato = S3;
			break;
		case S5:
			if((millis()-T>10*1000) && (millis()-T<20*1000)) stato = S2;
			break;
	}

	if(stato == S1){
		HL1 = LOW;
		K1 = LOW;
	}
	if(stato == S3){
		HL1 = HIGH;
		HAL = HIGH;
		K1 = HIGH;
	}
	if(stato == S4){
		HAL = HIGH;
		K1 = HIGH;
		HL1 = LOW;
	}
	if(stato == S5){
		HL1 = LOW;
	}

	if(oldStato != stato){
		T = millis();
		HAL = LOW;
		HAL = LOW;
		oldStato = stato;
	}

	digitalWrite(pin_HL1, HL1);
	digitalWrite(pin_K1, K1);
	digitalWrite(pin_HAL, HAL);
}