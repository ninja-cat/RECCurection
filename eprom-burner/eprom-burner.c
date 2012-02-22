/*****************************************************
Project : try attiny2313 and blinking LEDs 
MY SECOND BINARY CLOCK
Q = 1MHz
MCU = ATTiny2313
*****************************************************/

#include <avr/io.h>
#include <avr/iotn2313.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <avr/sleep.h>
#include <avr/wdt.h>

#define uint unsigned int
#define uchar unsigned char

#define SECONDS (20)
#define DELAY (2*SECONDS)
#define KEY_REPEATS (SECONDS*2)
#define LIGHT_DUR (10)

#define ADMIN (1)
#define WORK  (2)
#define BLINK (3)

static volatile uchar ticks, mins, hours, secs, lights_on, last_key, repeats, state=BLINK, KEYB, PREV_KEYB, delay;
static volatile uchar blink_hours=1, blink_mins=1<<5;

ISR (TIMER1_COMPA_vect)
{
		
	if (delay) { //delay after switching to ADMIN mode
		delay--;
		return;
	}

	// read "keyboard"

	KEYB=( ( ( (PINB & 192) >> 6 ) | ( (PIND & 32) >> 3 ))  ^ 0xFF ) & 7;

	if (KEYB ^ PREV_KEYB) {

		switch( KEYB ) {
			case 1 : // M++ pressed
				if (state==ADMIN) {
					mins++; 
				}
				last_key=0;
				break;
			case 2 : // H++ pressed
				if (state==ADMIN) {
					hours++;
				}
				last_key=0;
				break;
			case 4 : // START pressed
				if (state==ADMIN||state==BLINK) {
					state=WORK;
					ticks=0;
					secs=0;
				} else {
					if (state==WORK)
					       	lights_on=LIGHT_DUR*SECONDS;
				}
				break;
			default : 
				last_key=0;
				break;	
		}
	} else {
		if (KEYB==3) {
			if (state==ADMIN) {
			//		hours++;
			//		mins++;
					last_key=0;
				} else {
					last_key=1;
					if (last_key) { // counting repeats
						repeats++;	
					} else {
						repeats=0;
					}
					if (repeats>=KEY_REPEATS) { // switch to ADMIN mode
						repeats=0;
						state=ADMIN;
						delay=DELAY;
						secs=0;
					}
				}
	
		}
	}

	PREV_KEYB=KEYB;

	switch( state ) {

		case WORK : 
			if (ticks==SECONDS) {
				ticks=0;
				secs++;
			}
			if (secs==60) {
				secs=0;
				mins++;
			}
			if (mins==60) {
				mins=0;
				hours++;
			}

			if (hours==24)
				hours=0;

			if (lights_on) {
				PORTD=(mins %32) | ((mins & 32) << 1);
				PORTB=((hours & 16) >> 3) | ((hours & 8) >> 1) | ((hours & 4) << 1) | ((hours & 2) << 3 ) | ((hours & 1) << 5 );
				if (! (ticks/(SECONDS/2)) ) {
					PORTB=PORTB | _BV(PB0);
				}
				lights_on--;
			} else {
				PORTD=0;
				PORTB=0;
			}

			break;

		case ADMIN :

			if (mins==60)
				mins=0;
			if (hours==24)
				hours=0;
			PORTD=(mins %32) | ((mins & 32) << 1);
			PORTB=((hours & 16) >> 3) | ((hours & 8) >> 1) | ((hours & 4) << 1) | ((hours & 2) << 3 ) | ((hours & 1) << 5 );
//			PORTD=((mins & 32) >> 5) | ((mins & 16) >> 3) | ((mins & 8) >> 1) | ((mins & 4) << 1 ) | ((mins & 2) << 3 ) | ((mins & 1) << 6 );
//			PORTB=mins;
//			PORTB=hours;

			break;

		case BLINK :	

			ticks%=60;

			if ( (ticks/6) &1) {
				blink_hours>>=1;
			} else {
				blink_hours<<=1;
			}
			if ( (ticks/5) &1) {
				blink_mins<<=1;
			} else {
				blink_mins>>=1;
			}

			PORTB=blink_mins;
			PORTD=blink_hours;

			break;	

		default :
			break;
	}	
	
	PORTB=PORTB | _BV(PB6) | _BV(PB7);
	PORTD=PORTD | _BV(PD5) ;
	
	ticks++;

}




int main(void) {

	cli();
	wdt_disable();

	CLKPR=0x80;
	CLKPR=0x02; // cpu/8 // 0x3 = 2**3

	PORTB= _BV(PB6) | _BV(PB7);
	DDRB=PORTB ^ 0xFF;

	PORTD= _BV(PD5);
	DDRD=PORTD ^ 0xFF;

	TCCR0A=0x00;
	TCCR0B=0x00;
	TCNT0=0x00;
	OCR0A=0x00;
	OCR0B=0x00;

	TCCR1A=0x00; 
	TCCR1B=0x09; // clk/1
	TCNT1=0x00;
	ICR1=0x00;
	OCR1A=49999; // 50 ms // 3125
	OCR1B=0;

	GIMSK=0x00;
	MCUCR=0x00;

	TIMSK=0x40;

	USICR=0x00;

	ACSR=0x80;

	set_sleep_mode(SLEEP_MODE_IDLE);
	
	sei();

	for(;;) {
		sleep_mode();
	};
	return 0;
}
