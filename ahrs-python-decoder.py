#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: automaticdai
# Version: v0.1
#
# notes:
# 1. This python script will gather data from miniAHRS at port 'COM_PORT'. The
# gathered data will be sent to "HOST, PORT".
# 2. To run this script, the miniAHRS should be connencted by a usb-to-serial
# and a TCP server at "host" is also expected.
#
# issues:
# Known issus 1: if data 0xaa is in the payload, the message will be dropped
# Known issus 2: message from miniAHRS is not valid with checksum

import serial, socket, threading, sys
import logging
import traceback
import codecs
import binascii

from time import sleep

COM_PORT = "/dev/ttyUSB1"
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

        self._acc = [0.0, 0.0, 0.0]
        self._gyo = [0.0, 0.0, 0.0]
        self._mag = [0.0, 0.0, 0.0]

        self._fps = 0

        self.comm_buff = bytearray()


    def get_raw_data(self):
        return (self._acc, self._gyo, self._mag)


    def get_ahrs(self):
        return (self._roll, self._pitch, self._yaw)


    def get_fps(self):
        return self._fps


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
        packet_len = (idx_end - idx_init) - 1

        # if no init is found, empty the buffer
        if (idx_init == -1):
            print_debug_msg('::err: no init')
            self.comm_buff = bytearray()
        # if message has init, but no start or end, probably will come later
        elif ((idx_start == -1) or (idx_end == -1)):
            # drop everything before init flag, because these could be wilding
            # bytes that should from the previous packet
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
                    #print_hex(msg_payload)
                    msg_id = msg_payload[1]
                    # decode message type: AHRS
                    if (msg_id == 0xA1):
                        self._yaw = self.correct_data((msg_payload[2] << 8) + msg_payload[3])
                        self._pitch = self.correct_data((msg_payload[4] << 8) + msg_payload[5])
                        self._roll = self.correct_data((msg_payload[6] << 8) + msg_payload[7])
                        self._fps = msg_payload[17]
                    # decode message type: raw
                    elif (msg_id == 0xA2):
                        # acc
                        self._acc[0] = self.correct_data((msg_payload[2] << 8) + msg_payload[3])
                        self._acc[1] = self.correct_data((msg_payload[4] << 8) + msg_payload[5])
                        self._acc[2] = self.correct_data((msg_payload[6] << 8) + msg_payload[7])
                        # gyo
                        self._gyo[0] = self.correct_data((msg_payload[8] << 8) + msg_payload[9])
                        self._gyo[1] = self.correct_data((msg_payload[10] << 8) + msg_payload[11])
                        self._gyo[2] = self.correct_data((msg_payload[12] << 8) + msg_payload[13])
                        # mag
                        self._mag[0] = self.correct_data((msg_payload[14] << 8) + msg_payload[15])
                        self._mag[1] = self.correct_data((msg_payload[16] << 8) + msg_payload[17])
                        self._mag[2] = self.correct_data((msg_payload[18] << 8) + msg_payload[19])
                    else:
                        print_debug_msg('::err: undefined message type')
                # see 'known issue 1'
                else:
                    print_debug_msg(':err: length is incorrect')

                # put the reminder into global buffer
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
    # setup logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s-%(levelname)s: %(message)s]',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # a miniAHRS object
    ahrs = miniAHRS()

    try:
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.connect((HOST, PORT))
        with serial.Serial(COM_PORT, 115200, timeout = 0.010) as ser:
            while True:
                data = ser.read(50)
                if len(data) > 0:
                    ahrs.decode(data)
                    (roll, pitch, yaw) = ahrs.get_ahrs()
                    (acc, gyo, mag) = ahrs.get_raw_data()
                    print((acc, gyo, mag, roll, pitch, yaw, ahrs.get_fps()))
                    # build a packet and send out
                    #b = bytearray()
                    #b.extend('{},{},{}\n'.format(roll, pitch, yaw).encode())
                    #print_debug_msg(b)
                    #s.sendall(b)
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        #ser.close()
