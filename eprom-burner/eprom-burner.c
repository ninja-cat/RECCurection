/*****************************************************
Project : eprom-burner
Q = 3.6864MHz
MCU = ATMEGA16A
*****************************************************/

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <util/crc16.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <string.h>

#define uint unsigned int
#define uchar unsigned char

#define CRC16_LEN (2)
#define PAGE_LEN  (2)
#define PAGE_SIZE (256)

static volatile uchar accepted_cmd;
static volatile uint max_rx_len, count_rx;

void (*run_cmd)();

uchar rx_buf[PAGE_LEN + PAGE_SIZE + CRC16_LEN];

void _cmd_identify(){
    // send ident string
    return;
}

void _cmd_read(){
    // read (ep)rom page
    return;
}

void _cmd_write(){
    // write eprom page
    return;
}

// USART byte received interrupt routine
ISR (USART_RXC_vect){

    uchar data = UDR;
    if (!accepted_cmd) {
        // waiting for the cmd name;
        // 'i','r','w
        switch (data){
            case 'i':
                // 'identify' cmd accepted
                max_rx_len = CRC16_LEN;
                count_rx = 0;
                accepted_cmd = 1;
                memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);
                run_cmd = _cmd_identify;
                break;
            case 'r':
                // 'read' (ep)rom page
                max_rx_len = PAGE_LEN + CRC16_LEN;
                count_rx = 0;
                accepted_cmd = 1;
                memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);
                run_cmd = _cmd_read;
                break;
            case 'w':
                // 'write' eprom page
                max_rx_len = PAGE_LEN + PAGE_SIZE + CRC16_LEN;
                count_rx = 0;
                accepted_cmd = 1; 
                memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);
                run_cmd = _cmd_write;
                break;
            default:
                accepted_cmd = 0;
                break;            
        }
    } else {
        // cmd was already accepted
        // read cmd params and data
        rx_buf[count_rx] = data;
        count_rx ++;
        if (count_rx == max_rx_len) {
            // all data was received
            // execute command
            run_cmd();
        }
    }
}

void _init_ports(){
    //todo
}

void _init_usart(){
    //todo
}

int main(void) {

	cli();
	wdt_disable();

	PORTB= _BV(PB6) | _BV(PB7);
	DDRB=PORTB ^ 0xFF;

	PORTD= _BV(PD5);
	DDRD=PORTD ^ 0xFF;

	MCUCR=0x00;

	ACSR=0x80;

	set_sleep_mode(SLEEP_MODE_IDLE);
	
	sei();

	for(;;) {
		sleep_mode();
	};
	return 0;
}
