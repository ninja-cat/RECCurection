###############################################################################
# Makefile for the project eprom-burner from RECCurection
###############################################################################

## General Flags
PROJECT = eprom-burner
MCU = atmega32
TARGET = eprom-burner.elf
CC = avr-gcc
CPU_CLK = 8000000
USART_BAUDRATE = 38400
## Options common to compile, link and assembly rules
COMMON = -mmcu=$(MCU)
GCC_OPTIMISATION_LEVEL = -Os
## Compile options common for all C compilation units.
CFLAGS = $(COMMON)
CFLAGS += -DF_CPU=$(CPU_CLK)UL
CFLAGS += -DUSART_BAUDRATE=$(USART_BAUDRATE)UL
CFLAGS += $(GCC_OPTIMISATION_LEVEL)
CFLAGS += -Wall -gdwarf-2 --combine -fwhole-program -ffunction-sections -fdata-sections -Wl,--relax,--gc-sections
CFLAGS += -Wp,-M,-MP,-MT,$(*F).o

## Linker flags
LDFLAGS = $(COMMON)

## Intel Hex file production flags
HEX_FLASH_FLAGS = -R .eeprom

HEX_EEPROM_FLAGS = -j .eeprom
HEX_EEPROM_FLAGS += --set-section-flags=.eeprom="alloc,load"
HEX_EEPROM_FLAGS += --change-section-lma .eeprom=0


## Objects that must be built in order to link
OBJECTS = eprom-burner.o 

## Build
all: $(TARGET) eprom-burner.hex eprom-burner.eep

## Compile
eprom-burner.o: eprom-burner.c
	$(CC) $(INCLUDES) $(CFLAGS) -c  $<

asm: 
	$(CC) $(INCLUDES) $(CFLAGS) -S  $<
##Link
$(TARGET): $(OBJECTS)
	 $(CC) $(LDFLAGS) $(OBJECTS) $(LIBDIRS) $(LIBS) -o $(TARGET)

%.hex: $(TARGET)
	avr-objcopy -O ihex $(HEX_FLASH_FLAGS)  $< $@

%.eep: $(TARGET)
	avr-objcopy $(HEX_EEPROM_FLAGS) -O ihex $< $@

%.lss: $(TARGET)
	avr-objdump -h -S $< > $@

## Clean target
.PHONY: clean
clean:
	-rm -rf $(OBJECTS) eprom-burner.elf eprom-burner.hex eprom-burner.eep eprom-burner.s

