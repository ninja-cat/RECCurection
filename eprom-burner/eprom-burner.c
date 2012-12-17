/*****************************************************
Project : eprom-burner
Q = 8.000MHz
MCU = ATMEGA32A
*****************************************************/

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <util/crc16.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/pgmspace.h>
#include <string.h>

#define uint unsigned int
#define uchar unsigned char

#define nop() asm volatile ("nop")

#define BAUD_PRESCALE (((F_CPU / (USART_BAUDRATE * 16UL))) - 1) 

#define CRC16_LEN (2)
#define PAGE_LEN  (2)
#define PAGE_SIZE (256)

#define SET_FLG(reg, bit_flag) reg |= (1 << bit_flag)
#define UNSET_FLG(reg, bit_flag) reg &= ~ (1 << bit_flag)

#define PIN_CE (2)
#define PIN_OE (3)
#define PIN_PGM (4)

#define PIN_A16 (5)
#define PIN_A17 (6)
#define PIN_A18 (7)

#define SET_CE_HI SET_FLG(PORTD, PIN_CE)
#define SET_CE_LO UNSET_FLG(PORTD, PIN_CE)

#define SET_OE_HI SET_FLG(PORTD, PIN_OE)
#define SET_OE_LO UNSET_FLG(PORTD, PIN_OE)

#define SET_PGM_HI SET_FLG(PORTD, PIN_PGM)
#define SET_PGM_LO UNSET_FLG(PORTD, PIN_PGM)

#define SET_A16_HI SET_FLG(PORTD, PIN_A16)
#define SET_A16_LO UNSET_FLG(PORTD, PIN_A16)

#define SET_A17_HI SET_FLG(PORTD, PIN_A17)
#define SET_A17_LO UNSET_FLG(PORTD, PIN_A17)

#define SET_A18_HI SET_FLG(PORTD, PIN_A18)
#define SET_A18_LO UNSET_FLG(PORTD, PIN_A18)

#define PIN_PRG_A07_LE (0)
#define PIN_PRG_A814_LE (1)
#define PIN_DIR_PRG (2)
#define PIN_OE_PRG (3)
#define PIN_CE_PRG (4)

#define SET_PRG_A07_LE_HI SET_FLG(PORTB, PIN_PRG_A07_LE)
#define SET_PRG_A07_LE_LO UNSET_FLG(PORTB, PIN_PRG_A07_LE)

#define SET_PRG_A814_LE_HI SET_FLG(PORTB, PIN_PRG_A814_LE)
#define SET_PRG_A814_LE_LO UNSET_FLG(PORTB, PIN_PRG_A814_LE)

#define SET_PRG_DATA_READ UNSET_FLG(PORTB, PIN_DIR_PRG)
#define SET_PRG_DATA_WRITE SET_FLG(PORTB, PIN_DIR_PRG)

#define SET_PRG_DATA_OE_HI SET_FLG(PORTB, PIN_OE_PRG)
#define SET_PRG_DATA_OE_LO UNSET_FLG(PORTB, PIN_OE_PRG)

#define SET_PRG_CE_HI SET_FLG(PORTB, PIN_CE_PRG)
#define SET_PRG_CE_LO UNSET_FLG(PORTB, PIN_CE_PRG)


uchar ident[] PROGMEM = "RECCurection eprom-burner backend v0.1";

static uchar accepted_cmd;
static uint max_rx_len;
static uint count_rx;
static uint computed_crc;

void (*run_cmd)();

uchar rx_buf[PAGE_LEN + PAGE_SIZE + CRC16_LEN];

void _send_byte(uchar data){
    while ((UCSRA & (1 << UDRE)) == 0){
    };
    UDR = data;
}

void _cmd_identify(){
    uchar tmp;
    uchar i;
    uint crc = 0xffff;
    // send ident string
    for (i = 0; ; i ++){
        tmp = pgm_read_byte(&ident[i]);
        if (!tmp) {
            break;
        }
        _send_byte(tmp);
        crc = _crc16_update(crc, tmp);
    }
    // send crc16
    _send_byte( ((char *) &crc)[0]);
    _send_byte( ((char *) &crc)[1]);
}

void _set_addr_hi(uchar page_l, uchar page_h){
    // set A8-A15(A18)
    PORTB = page_l;
    if (page_h & _BV(0)){
        SET_A16_HI;
    } else {
        SET_A16_LO;
    }
    if (page_h & _BV(1)){
        SET_A17_HI;
    } else {
        SET_A17_LO;
    }
    if (page_h & _BV(2)){
        SET_A18_HI;
    } else {
        SET_A18_LO;
    }
}

void _cmd_fast_dump(){
    // read (ep)rom page
    uchar i;
    uint crc_r = 0xffff;
    PORTC = 0x00;
    DDRC = 0x00;

    SET_PRG_CE_HI;
    SET_PRG_DATA_OE_HI;
    SET_PRG_A07_LE_HI;
    SET_PRG_A814_LE_HI;
    SET_PRG_DATA_READ;
    DDRC = 0xff;
    PORTC = rx_buf[0];
    nop();
    SET_PRG_A814_LE_LO;
    memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);

    // read the memory page
    for (i = 0; ; i ++){
        DDRC = 0xff;
        SET_PRG_A07_LE_HI;
        PORTC = i;
        SET_PRG_A07_LE_LO;
        SET_PRG_CE_LO;
        PORTC = 0x00;
        DDRC = 0x00;
        SET_PRG_DATA_OE_LO;
        _delay_us(1);    
        rx_buf[i] = PINC;
        SET_PRG_DATA_OE_HI;
        SET_PRG_CE_HI;
        crc_r = _crc16_update(crc_r, rx_buf[i]);
        if (i == 0xff){
            break;
        }
    }
    PORTC = 0x00;
    DDRC = 0x00;
    // send the memory page
    for (i = 0; ; i ++){
        _send_byte(rx_buf[i]);
        if (i == 0xff){
            break;
        }
    }
    _send_byte( ((char *) &crc_r)[0]);
    _send_byte( ((char *) &crc_r)[1]);
}

void _cmd_read(){
    // read (ep)rom page
    uchar i;
    uint crc_r = 0xffff;
    SET_CE_LO;
    SET_OE_HI;
    _set_addr_hi(rx_buf[0], rx_buf[1]);
    memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);
    // read the memory page
    for (i = 0; ; i ++){
        // set A0-A7
        PORTA = i;
        SET_OE_LO;
        _delay_us(1);    
        rx_buf[i] = PINC;
        SET_OE_HI;
        crc_r = _crc16_update(crc_r, rx_buf[i]);
        if (i == 0xff){
            SET_CE_HI;
            break;
        }
    }
    // send the memory page
    for (i = 0; ; i ++){
        _send_byte(rx_buf[i]);
        if (i == 0xff){
            break;
        }
    }
    _send_byte( ((char *) &crc_r)[0]);
    _send_byte( ((char *) &crc_r)[1]);
}

void _cmd_write(){
    // write eprom page
    uchar i;
    uint crc_r = 0xffff;
    SET_CE_HI;
    SET_OE_HI;
    SET_PGM_HI;
    _set_addr_hi(rx_buf[0], rx_buf[1]);
    DDRC = 0xff;
    for (i = 0; ; i ++){
        // set A0-A7
        PORTA = i;
        PORTC = rx_buf[i + 2];
        SET_CE_LO;
        _delay_us(5);    
        SET_PGM_LO;
        _delay_us(100);
        SET_PGM_HI;
        _delay_us(5);    
        if (i == 0xff){
            SET_CE_HI;
            break;
        }
    }
    PORTC = 0x00;
    DDRC = 0x00;
    uchar reply[] = "done";
    for (i = 0; i < 4; i ++){
        _send_byte(reply[i]);
        crc_r = _crc16_update(crc_r, reply[i]);
    }
    _send_byte( ((char *) &crc_r)[0]);
    _send_byte( ((char *) &crc_r)[1]);
}

int _is_crc_correct(){
    // perform checksum check
    uint received_crc = * (uint *) &rx_buf[max_rx_len - CRC16_LEN];
    uint i;
    for (i = 0; i < max_rx_len - CRC16_LEN; ++ i){
        computed_crc = _crc16_update(computed_crc, rx_buf[i]);
    }
    if (computed_crc != received_crc){
        _send_byte('e');
        _send_byte( ((char *) & computed_crc)[0]);
        _send_byte( ((char *) & computed_crc)[1]);
        return -1;
    } else {
        _send_byte('a');
        _send_byte(0x7e);
        _send_byte(0xa8);
        return 0;
    }
}

// USART byte received interrupt service routine
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
            case 'f':
                // 'fast_dump' PRG page
                max_rx_len = PAGE_LEN + CRC16_LEN;
                count_rx = 0;
                accepted_cmd = 1;
                memset(rx_buf, 0, PAGE_LEN + PAGE_SIZE + CRC16_LEN);
                run_cmd = _cmd_fast_dump;
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
        };
        computed_crc = 0xffff;
        computed_crc = _crc16_update(computed_crc, data);
    } else {
        // cmd was already accepted
        // read cmd params and data
        rx_buf[count_rx] = data;
        count_rx ++;
        if (count_rx == max_rx_len) {
            // all data was received
            // execute command if crc is correct
            if (! _is_crc_correct()){
                run_cmd();
            }
            accepted_cmd = 0;
        }
    }
}

void _init_ports(){
    // PORT C is 8bit data input from (EP)ROM, switch to hi-Z state
    PORTC = 0x00;
    DDRC = 0x00;
    // PORT A & B are address lines outputs
    PORTA = 0x00;
    DDRA = 0xff;
    PORTB = 0x00;
    DDRB = 0xff;
    // these ports cover only 16 address lines, but 27C010 has 17;
    // first to bits (0,1) of PORT D are ised for usart;
    PORTD = PORTD & (_BV(0) | _BV(1));
    // PD2 is #CE
    SET_CE_HI;
    // PD3 is #OE
    SET_OE_HI;
    // PD4 is #PGM
    SET_PGM_HI;
    // PD5 is A16
    // PD6/PD7 reserved for A17/A18, but not used;
    DDRD |= _BV(7) | _BV(6) | _BV(5) | _BV(4) | _BV(3) | _BV(2);
}

void _init_usart(){
    UCSRB |= (1 << RXEN) | (1 << TXEN);   // Turn on the transmission and reception circuitry 
    UCSRB |= (1 << RXCIE); // Enable the USART Recieve Complete interrupt (USART_RXC) 
    UCSRC |= (1 << URSEL) | (1 << UCSZ0) | (1 << UCSZ1); // Use 8-bit character sizes 
    UBRRH = (BAUD_PRESCALE >> 8); // Load upper 8-bits of the baud rate value into the high byte of the UBRR register 
    UBRRL = BAUD_PRESCALE; // Load lower 8-bits of the baud rate value into the low byte of the UBRR register 
}

int main(void){

    cli();
    wdt_disable();
    
    _init_usart();
    _init_ports();
   
    set_sleep_mode(SLEEP_MODE_IDLE);
    
    sei();

    for(;;){
        sleep_mode();
    };
    return 0;
}
