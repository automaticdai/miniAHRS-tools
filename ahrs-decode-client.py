# -*- coding: utf-8 -*-
# known issus 1: if 0xaa is in the payload, the message will be dropped 
import serial, socket, threading
import codecs
import binascii

from time import sleep

COM_PORT = "COM3"
HOST, PORT = "localhost", 8888

AHRS_COMM_INIT = 0xA5
AHRS_COMM_START = 0x5A
AHRS_COMM_END = 0xAA


def print_debug_msg(msg):
    print(msg)
   

def print_hex(hex_bytearray):
    print_debug_msg(binascii.hexlify(hex_bytearray))


class miniAHRS:
    def __init__(self):
        self._yaw = 0.0
        self._pitch = 0.0
        self._roll = 0.0
        
        self._acc = 0.0
        self._gyo = 0.0
        self._mag = 0.0

        self.comm_buff = bytearray()


    def get_raw_data(self):
        return (self._acc, self._gyo, self._mag)

        
    def get_ahrs(self):
        return (self._pitch, self._roll, self._yaw)

    
    # the miniAHRS has a bug for negative number
    # this function is used to correct that behaviour
    # this function also countact the scale factor of 10.0
    def correct_data(self, data):
        if (data >= 0x8000):
            data = -(data - 0x8000)
        return (data / 10.0)


    def decode(self, new_msg):
        print_debug_msg('::executing decode()')
        print_hex(new_msg)
        # push the new message into local buffer
        self.comm_buff.extend(new_msg)
        while (self.decode_once() and self.comm_buff):
            pass
        print_debug_msg('::exit decode()')


    def decode_once(self):
        print_debug_msg('::executing decode_once()')
        b_result = False        
        
        idx_init = self.comm_buff.find(AHRS_COMM_INIT)
        idx_start = self.comm_buff.find(AHRS_COMM_START)
        idx_end = self.comm_buff.find(AHRS_COMM_END)
        packet_len = (idx_end - idx_init - 2) + 1        
        
        # if no init is found, empty the buffer
        if (idx_init == -1):
            print_debug_msg('::err: no init')
            self.comm_buff = bytearray()
        # if message has init, but no start or end, probably comming later
        elif ((idx_start == -1) or (idx_end == -1)):
            # drop everything before init flag, because these are wilding 
            # bytes that should for the previous packet
            print_debug_msg('::err: no start or end')            
            self.comm_buff = self.comm_buff[idx_init:]
        # found init, start and end
        # but have to verify their locations
        else:
            if ((idx_start == idx_init + 1) and (idx_end > idx_start)):
                # get the payload of the message
                # this will remove init, start and end flags
                print_debug_msg((idx_init, idx_start, idx_end, packet_len))
                msg_payload = self.comm_buff[idx_start + 1:idx_end]
                msg_len = msg_payload[0]
                if (msg_len == packet_len):
                    print_hex(msg_payload)
                    msg_fun = msg_payload[1]
                    # decode message
                    if (msg_fun == 0xA1):               
                        self._yaw = self.correct_data((msg_payload[2] << 8) + msg_payload[3])
                        self._pitch = self.correct_data((msg_payload[4] << 8) + msg_payload[5])
                        self._roll = self.correct_data((msg_payload[6] << 8) + msg_payload[7])
                    elif (msg_fun == 0xA2):
                        pass
                    else:
                        print_debug_msg('::err: undefined message type')
                # see 'known issue 1'
                else:
                    print_debug_msg(':err: length incorrect')
                                
                # put reminder into global buffer
                self.comm_buff = self.comm_buff[idx_end + 1:]                
                b_result = True
            # found init, start and end, but at wrong places
            # two possiblities:
            # a) one of the flags is data not flag
            # b) the init of the first message is dropped, so the init of the second message is got 
            # case a) is very complicated and difficult to detect, so for the moment
            # we empty the whole buffer 
            else:
                print_debug_msg('::err: flags are in wrong positions')
                self.comm_buff = bytearray()
        
        print_hex(self.comm_buff)
        print_debug_msg('::exit decode_once()')
        return b_result


# test cases
a = codecs.decode(b'a55a12a1aa8a82878326800500fd278301e0ffaaa5','hex')
aa = codecs.decode(b'5a12a1038a82878326800500fd278301e0ffaa','hex')
aaa = codecs.decode(b'a55a12a1038a82878326800500fd278301e0ffaa','hex')
b = codecs.decode(b'a55a16a2b9199a23042f80100006800400780035805819aaa55a12a1038a82878326800500fd278301e0ffaa','hex')


if __name__ == '__main__':
    
    ahrs = miniAHRS()

    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((HOST, PORT))
    #s.sendall(b'\n--------------------------------------\n')
    
    with serial.Serial(COM_PORT, 115200, timeout = 0.02) as ser:
        while True:
            data = ser.read(100)
            if len(data) > 0:
                ahrs.decode(data)
                (pitch, roll, yaw) = ahrs.get_ahrs()
                print((pitch, roll, yaw))
                print('\r\n')
                #b = bytearray()
                #b.extend('{} {} {}\n'.format(yaw, pitch, roll).encode())
                #print_debug_msg(b)
                #s.sendall(b)

    #s.close()
    
