#!/usr/bin/python

from datetime import datetime
import argparse
import os


import serial


class MyException(Exception):
    def __str__(self):
        pass

class NoResponseError(MyException):
    def __str__(self):
        return repr("Timeout: no response from backend") 

class NotEnoughDataReceived(MyException):
    def __str__(self):
        return repr("Received data length differs from expected") 

class CorruptedDataReceived(MyException):
    def __str__(self):
        return repr("Corrupted data received") 

class CorruptedDataTransmitted(MyException):
    def __str__(self):
        return repr("Corrupted data transmitted") 

class UnacceptableReply(MyException):
    def __str__(self):
        return repr("Unacceptable reply from backend") 


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


def crc16_calc(data):
    crc = 0xFFFF
    for i in xrange(0, len(data), 1):
        crc = (crc >> 8) ^ _crc16_table[(crc & 0xFF) ^ ord(data[i])]
    return chr(crc & 0xFF) + chr(crc >> 8)


def port_read(port, len_t):
    response = port.read(len_t)
    if not response:
        raise NoResponseError()
    if len(response) != len_t:
        raise NotEnoughDataReceived()
    if crc16_calc(response[:-2]) != response[-2:]:
        raise CorruptedDataReceived()
    return response


def port_write(port, data):
    port.write(data)


def issue_cmd(cmd):
    format_cmd(cmd)
    port_write(cmd['port'], cmd['raw_data'])
    respons = port_read(cmd['port'], 3) # ack_size = 3
    if respons[0] == 'a':
        # command was accepted
        #print "backend accepted %s command" % cmd_name
        return port_read(cmd['port'], cmd['resp_len'])[:-2]
    elif respons[0] == 'e':
        # bad_crc
        print "bad crc transmitted to backend"
        raise CorruptedDataTransmitted()
    else:
        print "check the device connectivity and backend version"
        raise UnacceptableReply()


def format_cmd(cmd):
    # cmd {'opcode': XX, 'param': YY, 'data': ZZ}
    data = cmd['opcode']
    if 'param' in cmd:
        data += cmd['param']
    if 'page' in cmd:
        data += chr(cmd['page'] & 0xFF) + chr(cmd['page'] >> 8)
    if 'data' in cmd:
        data += cmd['data']
    data += crc16_calc(data)
    cmd['raw_data'] = data
    return cmd


def exec_check(**kwargs):
    cmd = kwargs['cmd']
    issue_cmd(cmd)
    print "backend is ready!"


def exec_fdump(**kwargs):
    args = kwargs['args']
    cmd = kwargs['cmd']
    args.size = 256
    f_name = args.outfile
    with open(f_name, "wb") as f:
        for page in xrange(0, args.size / 2, 1):
            cmd['page'] = page
            f.write(issue_cmd(cmd))
    print "FDUMP: successful: dumped %d bytes to %s file" % (os.path.getsize(f_name), f_name)


def exec_dump(**kwargs):
    args = kwargs['args']
    cmd = kwargs['cmd']
    f_name = args.outfile
    with open(f_name, "wb") as f:
        for page in xrange(0, args.size / 2, 1):
            cmd['page'] = page
            f.write(issue_cmd(cmd))
    print "DUMP: successful: dumped %d bytes to %s file" % (os.path.getsize(f_name), f_name)


def exec_burn(**kwargs):
    args = kwargs['args']
    cmd = kwargs['cmd']
    f_name = args.infile
    if not args.infile:
        raise Exception("input file is not specified, use \'-i\' option")
    if args.size * 128 != os.path.getsize(f_name):
        raise Exception("input file and rom size mismatch! "
                        "file size = %d, rom size = %d" % (os.path.getsize(f_name), args.size * 128))
    with open(f_name, "rb") as f:
        for page in xrange(0, args.size / 2, 1):
            cmd['page'] = page
            cmd['data'] = f.read(256)
            issue_cmd(cmd)
    print "BURN: successful: burnt %d bytes from %s file to eprom" % (args.size * 128, f_name)


if __name__ == "__main__":

    _acpt_cmds = ('dump', 'burn', 'check', 'fdump')

    def get_argparser():
        parser = argparse.ArgumentParser(
                description='EPROM dumper/burner CLI frontend tool',
                epilog='http://github.com/ninja-cat/RECCurection')
        parser.add_argument('command',
                            help='command to send: [%s]' % ", ".join(_acpt_cmds))
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

    args = get_argparser().parse_args()

    print args 
    try:
        ser = serial.Serial(port=args.serial_name,
                        baudrate=args.baudrate, bytesize=8,
                        parity='N', stopbits=1, timeout=0.5,
                        xonxoff=0, rtscts=0)
        cmd = args.command
        if cmd not in _acpt_cmds:
            raise Exception('acceptable commands are:\n'
                            '%s' % ("\n".join(_acpt_cmds)))
        cmd_packets = {
                        'check': {'opcode': 'i', 'resp_len': 40},
                        'dump': {'opcode': 'r', 'resp_len': 256 + 2},
                        'fdump': {'opcode': 'r', 'resp_len': 256 + 2},
                        'burn': {'opcode': 'w', 'resp_len': 4 + 2},
                      }                            
        args.outfile = args.outfile or datetime.now().isoformat() + ".%s" % cmd
        cmd_data = cmd_packets[cmd]
        cmd_data['port'] = ser
        eval("exec_%s" % cmd)(**{"args":args, "cmd":cmd_data})
    except Exception as e:
        print e
        exit(-1)
    else:
        exit(0)
