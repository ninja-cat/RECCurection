#!/usr/bin/python

from datetime import datetime
import argparse
import os


import serial


class MyException(Exception):
    def __init__(self):
        self.msg = "BWA-HA-HA-HA-H"

    def __str__(self):
        filter_list = ['data', 'raw_data']
        map(self.cmd.pop, filter(lambda x: x in self.cmd, filter_list))
        return "\nFAILURE REASON: %s\n\ncmd: %s" % (self.msg, self.cmd)


class NoResponseError(MyException):
    def __init__(self):
        self.msg = "Timeout: no response from backend"


class NotEnoughDataReceived(MyException):
    def __init__(self, resp_len, exp_len):
        self.msg = "Received data len={%d}, but expected len={%d}" % (resp_len,
                                                                      exp_len)


class CorruptedDataReceived(MyException):
    def __init__(self):
        self.msg = "Corrupted data received"


class CorruptedDataTransmitted(MyException):
    def __init__(self):
        self.msg = "Corrupted data transmitted"


class UnacceptableReply(MyException):
    def __init__(self):
        self.msg = "Unacceptable reply from backend"


_crc16_table = (
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040,
)


op_types = {
    'imm': {"len": 2, "fmt": "%s #$%02X"},
    'zp': {"len": 2, "fmt": "%s $%02X"},
    'zpx': {"len": 2, "fmt": "%s $%02X,X"},
    'zpy': {"len": 2, "fmt": "%s $%02X,Y"},
    'ab': {"len": 3, "fmt": "%s $%02X%02X"},
    'abx': {"len": 3, "fmt": "%s $%02X%02X,X"},
    'aby': {"len": 3, "fmt": "%s $%02X%02X,Y"},
    'in': {"len": 3, "fmt": "%s ($%02X%02X)"},
    'inx': {"len": 2, "fmt": "%s ($%02X,X)"},
    'iny': {"len": 2, "fmt": "%s ($%02X),Y"},
    'imp': {"len": 1, "fmt": "%s"},
    'br': {"len": 2, "fmt": "%s $%04X"},
    }

ops = {
    '??': {'str': '???', 'type': 'imp'},
    '69': {'str': 'ADC', 'type': 'imm'},
    '65': {'str': 'ADC', 'type': 'zp'},
    '75': {'str': 'ADC', 'type': 'zpx'},
    '6D': {'str': 'ADC', 'type': 'ab'},
    '7D': {'str': 'ADC', 'type': 'abx'},
    '79': {'str': 'ADC', 'type': 'aby'},
    '61': {'str': 'ADC', 'type': 'inx'},
    '71': {'str': 'ADC', 'type': 'iny'},
    '29': {'str': 'AND', 'type': 'imm'},
    '25': {'str': 'AND', 'type': 'zp'},
    '35': {'str': 'AND', 'type': 'zpx'},
    '2D': {'str': 'AND', 'type': 'ab'},
    '3D': {'str': 'AND', 'type': 'abx'},
    '39': {'str': 'AND', 'type': 'aby'},
    '21': {'str': 'AND', 'type': 'inx'},
    '31': {'str': 'AND', 'type': 'iny'},
    '0A': {'str': 'ASL A', 'type': 'imp'},
    '06': {'str': 'ASL', 'type': 'zp'},
    '16': {'str': 'ASL', 'type': 'zpx'},
    '0E': {'str': 'ASL', 'type': 'ab'},
    '1E': {'str': 'ASL', 'type': 'abx'},
    '24': {'str': 'BIT', 'type': 'zp'},
    '2C': {'str': 'BIT', 'type': 'ab'},
    '10': {'str': 'BPL', 'type': 'br'},
    '30': {'str': 'BMI', 'type': 'br'},
    '50': {'str': 'BVC', 'type': 'br'},
    '70': {'str': 'BVS', 'type': 'br'},
    '90': {'str': 'BCC', 'type': 'br'},
    'B0': {'str': 'BCS', 'type': 'br'},
    'D0': {'str': 'BNE', 'type': 'br'},
    'F0': {'str': 'BEQ', 'type': 'br'},
    '00': {'str': 'BRK', 'type': 'imp'},
    'C9': {'str': 'CMP', 'type': 'imm'},
    'C5': {'str': 'CMP', 'type': 'zp'},
    'D5': {'str': 'CMP', 'type': 'zpx'},
    'CD': {'str': 'CMP', 'type': 'ab'},
    'DD': {'str': 'CMP', 'type': 'abx'},
    'D9': {'str': 'CMP', 'type': 'aby'},
    'C1': {'str': 'CMP', 'type': 'inx'},
    'D1': {'str': 'CMP', 'type': 'iny'},
    'E0': {'str': 'CPX', 'type': 'imm'},
    'E4': {'str': 'CPX', 'type': 'zp'},
    'EC': {'str': 'CPX', 'type': 'ab'},
    'C0': {'str': 'CPY', 'type': 'imm'},
    'C4': {'str': 'CPY', 'type': 'zp'},
    'CC': {'str': 'CPY', 'type': 'ab'},
    'C6': {'str': 'DEC', 'type': 'zp'},
    'D6': {'str': 'DEC', 'type': 'zpx'},
    'CE': {'str': 'DEC', 'type': 'ab'},
    'DE': {'str': 'DEC', 'type': 'abx'},
    '49': {'str': 'EOR', 'type': 'imm'},
    '45': {'str': 'EOR', 'type': 'zp'},
    '55': {'str': 'EOR', 'type': 'zpx'},
    '4D': {'str': 'EOR', 'type': 'ab'},
    '5D': {'str': 'EOR', 'type': 'abx'},
    '59': {'str': 'EOR', 'type': 'aby'},
    '41': {'str': 'EOR', 'type': 'inx'},
    '51': {'str': 'EOR', 'type': 'iny'},
    '18': {'str': 'CLC', 'type': 'imp'},
    '38': {'str': 'SEC', 'type': 'imp'},
    '58': {'str': 'CLI', 'type': 'imp'},
    '78': {'str': 'SEI', 'type': 'imp'},
    'B8': {'str': 'CLV', 'type': 'imp'},
    'D8': {'str': 'CLD', 'type': 'imp'},
    'F8': {'str': 'SED', 'type': 'imp'},
    'E6': {'str': 'INC', 'type': 'zp'},
    'F6': {'str': 'INC', 'type': 'zpx'},
    'EE': {'str': 'INC', 'type': 'ab'},
    'FE': {'str': 'INC', 'type': 'abx'},
    '4C': {'str': 'JMP', 'type': 'ab'},
    '6C': {'str': 'JMP', 'type': 'in'},
    '20': {'str': 'JSR', 'type': 'ab'},
    'A9': {'str': 'LDA', 'type': 'imm'},
    'A5': {'str': 'LDA', 'type': 'zp'},
    'B5': {'str': 'LDA', 'type': 'zpx'},
    'AD': {'str': 'LDA', 'type': 'ab'},
    'BD': {'str': 'LDA', 'type': 'abx'},
    'B9': {'str': 'LDA', 'type': 'aby'},
    'A1': {'str': 'LDA', 'type': 'inx'},
    'B1': {'str': 'LDA', 'type': 'iny'},
    'A2': {'str': 'LDX', 'type': 'imm'},
    'A6': {'str': 'LDX', 'type': 'zp'},
    'B6': {'str': 'LDX', 'type': 'zpy'},
    'AE': {'str': 'LDX', 'type': 'ab'},
    'BE': {'str': 'LDX', 'type': 'aby'},
    'A0': {'str': 'LDY', 'type': 'imm'},
    'A4': {'str': 'LDY', 'type': 'zp'},
    'B4': {'str': 'LDY', 'type': 'zpx'},
    'AC': {'str': 'LDY', 'type': 'ab'},
    'BC': {'str': 'LDY', 'type': 'abx'},
    '4A': {'str': 'LSR A', 'type': 'imp'},
    '46': {'str': 'LSR', 'type': 'zp'},
    '56': {'str': 'LSR', 'type': 'zpx'},
    '4E': {'str': 'LSR', 'type': 'ab'},
    '5E': {'str': 'LSR', 'type': 'abx'},
    'EA': {'str': 'NOP', 'type': 'imp'},
    '09': {'str': 'ORA', 'type': 'imm'},
    '05': {'str': 'ORA', 'type': 'zp'},
    '15': {'str': 'ORA', 'type': 'zpx'},
    '0D': {'str': 'ORA', 'type': 'ab'},
    '1D': {'str': 'ORA', 'type': 'abx'},
    '19': {'str': 'ORA', 'type': 'aby'},
    '01': {'str': 'ORA', 'type': 'inx'},
    '11': {'str': 'ORA', 'type': 'iny'},
    'AA': {'str': 'TAX', 'type': 'imp'},
    '8A': {'str': 'TXA', 'type': 'imp'},
    'CA': {'str': 'DEX', 'type': 'imp'},
    'E8': {'str': 'INX', 'type': 'imp'},
    'A8': {'str': 'TAY', 'type': 'imp'},
    '98': {'str': 'TYA', 'type': 'imp'},
    '88': {'str': 'DEY', 'type': 'imp'},
    'C8': {'str': 'INY', 'type': 'imp'},
    '2A': {'str': 'ROL A', 'type': 'imp'},
    '26': {'str': 'ROL', 'type': 'zp'},
    '36': {'str': 'ROL', 'type': 'zpx'},
    '2E': {'str': 'ROL', 'type': 'ab'},
    '3E': {'str': 'ROL', 'type': 'abx'},
    '6A': {'str': 'ROR A', 'type': 'imp'},
    '66': {'str': 'ROR', 'type': 'zp'},
    '76': {'str': 'ROR', 'type': 'zpx'},
    '6E': {'str': 'ROR', 'type': 'ab'},
    '7E': {'str': 'ROR', 'type': 'abx'},
    '40': {'str': 'RTI', 'type': 'imp'},
    '60': {'str': 'RTS', 'type': 'imp'},
    'E9': {'str': 'SBC', 'type': 'imm'},
    'E5': {'str': 'SBC', 'type': 'zp'},
    'F5': {'str': 'SBC', 'type': 'zpx'},
    'ED': {'str': 'SBC', 'type': 'ab'},
    'FD': {'str': 'SBC', 'type': 'abx'},
    'F9': {'str': 'SBC', 'type': 'aby'},
    'E1': {'str': 'SBC', 'type': 'inx'},
    'F1': {'str': 'SBC', 'type': 'iny'},
    '85': {'str': 'STA', 'type': 'zp'},
    '95': {'str': 'STA', 'type': 'zpx'},
    '8D': {'str': 'STA', 'type': 'ab'},
    '9D': {'str': 'STA', 'type': 'abx'},
    '99': {'str': 'STA', 'type': 'aby'},
    '81': {'str': 'STA', 'type': 'inx'},
    '91': {'str': 'STA', 'type': 'iny'},
    '9A': {'str': 'TXS', 'type': 'imp'},
    'BA': {'str': 'TSX', 'type': 'imp'},
    '48': {'str': 'PHA', 'type': 'imp'},
    '68': {'str': 'PLA', 'type': 'imp'},
    '08': {'str': 'PHP', 'type': 'imp'},
    '28': {'str': 'PLP', 'type': 'imp'},
    '86': {'str': 'STX', 'type': 'zp'},
    '96': {'str': 'STX', 'type': 'zpy'},
    '8E': {'str': 'STX', 'type': 'ab'},
    '84': {'str': 'STY', 'type': 'zp'},
    '94': {'str': 'STY', 'type': 'zpx'},
    '8C': {'str': 'STY', 'type': 'ab'},
    }


cmd_packets = {
                'check': {'opcode': 'i', 'resp_len': 40},
                'dump': {'opcode': 'r', 'resp_len': 256 + 2},
                'fdump': {'opcode': 'f', 'resp_len': 256 + 2},
                'burn': {'opcode': 'w', 'resp_len': 4 + 2},
              }


def dis_asm(**kwargs):
    def _to_signed(byte):
        return ((byte + 128) & 0xff) - 128

    args = kwargs['args']
    f_name = args.infile
    if not args.infile:
        raise Exception("input file is not specified, use \'-i\' option")
    with open(f_name, "rb") as f:
        data = f.read()
        #import pdb; pdb.set_trace()
        off_s = 0x8000
        pc = off_s
        while pc < 0xfffa:
            cur = pc - off_s
            h_op = "%02X" % ord(data[cur])
            params = [pc]
            byte = h_op
            if h_op not in ops:
                h_op = '??'
            o_type = ops[h_op]['type']
            ln = op_types[o_type]['len']
            params.append(byte + ' %02X' * (ln - 1) % tuple(map(ord,
                                                    data[cur + 1: cur + ln]))
                               + ' ' * (3 - ln) * 3)
            params.append(ops[h_op]['str'])
            if o_type == 'br':
                params.append(pc + ln + _to_signed(ord(data[cur + 1])))
            else:
                for yy in reversed(range(1, ln)):
                    params.append(ord(data[cur + yy]))
            ss = "%04X: %s | " + op_types[o_type]['fmt']
            print ss % tuple(params)
            pc += ln
        pc = 0xfffa
        for zz in ('NMI', 'RST', 'IRQ'):
            print "%04X: %s %02X%02X" % (pc, zz, ord(data[pc - off_s + 1]),
                                                        ord(data[pc - off_s]))
            pc += 2


def exception_wrap(f):
    def _wrapped(cmd):
        try:
            return f(cmd)
        except Exception as e:
            e.cmd = cmd
            raise e
    return _wrapped


@exception_wrap
def issue_cmd(cmd):
    def _crc16_calc(data):
        crc = 0xFFFF
        for i in xrange(0, len(data), 1):
            crc = (crc >> 8) ^ _crc16_table[(crc & 0xFF) ^ ord(data[i])]
        return chr(crc & 0xFF) + chr(crc >> 8)

    def _port_read(port, len_t):
        response = port.read(len_t)
        if not response:
            raise NoResponseError()
        if len(response) != len_t:
            raise NotEnoughDataReceived(len(response), len_t)
        if _crc16_calc(response[:-2]) != response[-2:]:
            raise CorruptedDataReceived()
        return response

    def _port_write(port, data):
        port.write(data)

    def _format_cmd(cmd):
        # cmd {'opcode': XX, 'param': YY, 'data': ZZ}
        data = cmd['opcode']
        if 'param' in cmd:
            data += cmd['param']
        if 'page' in cmd:
            data += chr(cmd['page'] & 0xFF) + chr(cmd['page'] >> 8)
        if 'data' in cmd:
            data += cmd['data']
        data += _crc16_calc(data)
        cmd['raw_data'] = data
        return cmd

    _format_cmd(cmd)
    _port_write(cmd['port'], cmd['raw_data'])
    respons = _port_read(cmd['port'], 3)  # ack_size = 3
    if respons[0] == 'a':
        # command was accepted
        return _port_read(cmd['port'], cmd['resp_len'])[:-2]
    elif respons[0] == 'e':
        # bad_crc
        print "bad crc transmitted to backend"
        raise CorruptedDataTransmitted()
    else:
        print "check the device connectivity and backend version"
        raise UnacceptableReply()


def check_backend(f):
    def _wrapped(**kwargs):
        try:
            check_cmd = cmd_packets['check']
            check_cmd['port'] = kwargs['cmd']['port']
            print "ready! got response: '%s'" % issue_cmd(**{"cmd": check_cmd})
            return f(**kwargs)
        except Exception as e:
            raise e
    return _wrapped


@check_backend
def exec_dump(**kwargs):
    args = kwargs['args']
    cmd = kwargs['cmd']
    if cmd['opcode'] == 'f':
        args.size = 256
    f_name = args.outfile
    with open(f_name, "wb") as f:
        for page in xrange(0, args.size / 2, 1):
            cmd['page'] = page
            f.write(issue_cmd(cmd))
    return {'file': f_name, 'done': 'to'}


@check_backend
def exec_burn(**kwargs):
    args = kwargs['args']
    cmd = kwargs['cmd']
    f_name = args.infile
    if not args.infile:
        raise Exception("input file is not specified, use \'-i\' option")
    if args.size * 128 != os.path.getsize(f_name):
        raise Exception("input file and rom size mismatch! "
              "file size = %d, rom size = %d" % (os.path.getsize(f_name),
                                                            args.size * 128))
    with open(f_name, "rb") as f:
        for page in xrange(0, args.size / 2, 1):
            cmd['page'] = page
            cmd['data'] = f.read(256)
            issue_cmd(cmd)
    return {'file': f_name, 'done': 'from'}


if __name__ == "__main__":

    @check_backend
    def _nop(**noop):
        pass

    _cmds = {
            'dump': exec_dump,
            'fdump': exec_dump,
            'burn': exec_burn,
            'check': _nop,
            'dis': dis_asm,
            }

    def _get_argparser():
        parser = argparse.ArgumentParser(
                description='EPROM dumper/burner CLI frontend tool',
                epilog='http://github.com/ninja-cat/RECCurection')
        parser.add_argument('command',
                            choices=_cmds.keys(),
                            help='command: [%s]' % ", ".join(_cmds.keys()))
        parser.add_argument('-O', dest='outfile', nargs='?',
                            help='output file')
        parser.add_argument('-i', dest='infile', nargs='?',
                            help='input file')
        parser.add_argument('-s', dest='size', nargs='?', type=int,
                            default=1024,
                            help='rom size in kbits. E.g. 256 for 27c256')
        parser.add_argument('-p', dest='serial_name', nargs='?',
                            default='/dev/ttyS0',
                            help='serial port. E.g. /dev/ttyS0')
        parser.add_argument('-b', dest='baudrate', nargs='?', type=int,
                            default=38400,
                            help='USART baud rate. E.g. 38400')

        return parser

    args = _get_argparser().parse_args()

    print args
    try:
        ser = serial.Serial(port=args.serial_name,
                        baudrate=args.baudrate, bytesize=8,
                        parity='N', stopbits=1, timeout=0.5,
                        xonxoff=0, rtscts=0)
        cmd = args.command
        args.outfile = args.outfile or datetime.now().isoformat() + ".%s" % cmd
        cmd_data = {}
        if cmd in cmd_packets:
            cmd_data = cmd_packets[cmd]
        cmd_data['port'] = ser
        strs = _cmds[cmd](**{"args": args, "cmd": cmd_data})
        if strs:
            print "%s: successful: %sed %d bytes %s %s file" % (cmd.upper(),
                cmd, os.path.getsize(strs['file']), strs['done'], strs['file'])
    except Exception as e:
        print e
        exit(-1)
    else:
        exit(0)
