#!/usr/bin/python

import argparse
import os


header_size = 16


def parse_ines_header(header):
# 0-3: Constant $4E $45 $53 $1A ("NES" followed by MS-DOS end-of-file) 
# 4: Size of PRG ROM in 16 KB units 
# 5: Size of CHR ROM in 8 KB units (Value 0 means the board uses CHR RAM) 
# 6: Flags 6 
# 7: Flags 7 
# 8: Size of PRG RAM in 8 KB units (Value 0 infers 8 KB for compatibility) 
# 9: Flags 9 
# 10: Flags 10 (unofficial) 
# 11-15: Zero filled
    
    if header[:4] != chr(0x4E) + chr(0x45) + chr(0x53) + chr(0x1A):
        raise Exception('INES header expected! Did you try to open .nes file?')
    
    ines_info = {} 
    ines_info['prg_size_bytes'] = ord(header[4]) * 1024 * 16
    ines_info['chr_size_bytes'] = ord(header[5]) * 1024 * 8
    
    return ines_info


def get_argparser():
    parser = argparse.ArgumentParser(
            description='tool for splitting .nes files (INES) '
                        'into PRG and CHR rom files',
            epilog='this is the part of RECCurection project, '
                   'check it out at http://github.com/ninja-cat/RECCurection')
    parser.add_argument('file',
                        help='a file to split')
    parser.add_argument('-O', dest='outfile', nargs='?',
                        help='an output file')
    
    return parser


if __name__ == "__main__":

    args = get_argparser().parse_args()

    try:
        with open(args.file, "rb") as f:
            header = f.read(header_size)
            info = parse_ines_header(header)
            prg_rom = f.read(info['prg_size_bytes'])
            chr_rom = f.read(info['chr_size_bytes'])
            chr_filename = os.path.splitext(args.file)[0]
            if args.outfile:
                chr_filename = args.outfile
            prg_filename = chr_filename
            chr_filename += '.chr'
            prg_filename += '.prg'
            with open(prg_filename, "wb") as prg_f:
                prg_f.write(prg_rom)
            with open(chr_filename, "wb") as chr_f:
                chr_f.write(prg_rom)

    except Exception as e:
        print e
        exit(-1)
