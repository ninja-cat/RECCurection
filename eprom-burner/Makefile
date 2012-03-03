###############################################################################
# Makefile for the project eprom-burner from RECCurection
###############################################################################

## General Flags
PROJECT = eprom-burner
MCU = atmega16
TARGET = eprom-burner.elf
CC = avr-gcc
CPU = 8000000

## Options common to compile, link and assembly rules
COMMON = -mmcu=$(MCU)

## Compile options common for all C compilation units.
CFLAGS = $(COMMON)
CFLAGS += -Wall -gdwarf-2 -Os -DF_CPU=$(CPU)UL --combine -fwhole-program -ffunction-sections -fdata-sections -Wl,--relax,--gc-sections
CFLAGS += -Wp,-M,-MP,-MT,$(*F).o

## Assembly specific flags
ASMFLAGS = $(COMMON)
ASMFLAGS += -x assembler-with-cpp -Wa,-gdwarf2

## Linker flags
LDFLAGS = $(COMMON)
LDFLAGS += 


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

