import serial, socket, threading
import binascii

from time import sleep

COM_PORT = "COM3"
HOST, PORT = "localhost", 8888

key = bytearray([0xA5, 0x5A, 0x12, 0xA1, 0x08, 0x00])


class miniAHRS:    
    def __init(self):
        self._yaw = 0
        self._pitch = 0
        self._roll = 0
        
        self._acc = 0
        self._gyo = 0
        self._mag = 0
    
    def decode(self, data):   
        _len = 0
        _state = 0    

        # decode header    
        for i in data:
            if _state == 0:
                if i == 0xa5:
                    _state = 1
            elif _state == 1:
                if i == 0x5a:
                    _state = 2
                else:
                    _state = 0
            elif _state == 2:
                _len = i
                if _len == 0x12:
                    _state = 3
                else:
                    _state = 0
            elif _state == 3:
                # 0xA1 (for processed) or 0xA2 (for raw data)
                    _state = 4
        # decode payload
        # try to analyze next frame
            elif _state == 4:
                    self._yaw = i
                    _state = 5
            elif _state == 5:
                    self._yaw = ((self._yaw  << 8) + i)
                    if self._yaw >= 0x8000:
                       self._yaw = -(self._yaw - 0x8000)
                    _state = 6                    
            elif _state == 6:
                    self._pitch = i
                    _state = 7
            elif _state == 7:
                    self._pitch = ((self._pitch  << 8) + i)
                    if self._pitch >= 0x8000:
                       self._pitch = -(self._pitch - 0x8000)
                    _state = 8
            elif _state == 8:
                    self._roll = i
                    _state = 9
            elif _state == 9:
                    self._roll = ((self._roll  << 8) + i)
                    if self._roll >= 0x8000:
                       self._roll = -(self._roll - 0x8000)                   
                    break
            else:
                _state = 0
                    
        return (self._yaw / 10.0, self._pitch / 10.0, self._roll / 10.0)

        
    
if __name__ == '__main__':
    
    ahrs = miniAHRS()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(b'\n--------------------------------------\n')
    
    with serial.Serial(COM_PORT, 115200, timeout = 0.05) as ser:
        while True:
            data = ser.read(50)
            if len(data) > 0:
                print(binascii.hexlify(data))
                (yaw, pitch, roll) = ahrs.decode(data)
                b = bytearray()
                b.extend('{} {} {}\n'.format(yaw, pitch, roll).encode())
                s.sendall(b)

    s.close()