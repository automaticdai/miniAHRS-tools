# miniAHRS-tools

The miniAHRS is an AHRS module that has an on-board MPU6050, a HMC5883L and a STM32F103T8 for AHRS applications. It is original produced by the Codehiplab7. 

This toolbox has the following tools for miniAHRS:

- ahrs-python-decoder: fetch stream data from serial port of the miniAHRS, decode protocol and display processed data.
- ahrs-visualisor: display the result in a 3D graphic interface.

AHRS: "An attitude and heading reference system (AHRS) consists of sensors on three axes that provide attitude information for aircraft, including roll, pitch and yaw." --- Wikipedia. 

## Usage

- Connect the mniAHRS through serial port.
- Run `python3 ahrs-python-decoder.py`


## Communication Protocol
The miniAHRS uses byte streams to communicate with a host machine.

### 1. IMU data message
- {0,1} start: 0xA5 0x5A
- {2} message size: 0x12 (18 bytes)
- {3} message identifier: 0xA1 (IMU)
- {4,5} Yaw: unit 0.1 degree. 0 - > 3600 map to 0 -> 360.0 degree
- {6,7} Pitch: unit 0.1 degree. -900 - 900 map to -90.0 -> 90.0 degree
- {8,9} Roll: unit 0.1 degree. -1800 -> 1800 map to -180.0 - > 180.0 degree
- {10,11} attitude, unit: 0.1m
- {12,13} temperature, unit: 0.1
- {14,15} barometric pressure, unit: 10Pa
- {16} IMU decode speed (per second)。
- {17} Checksum: sum all the data apart from the start, and get the lower byte.
- {18} end: 0xAA


### 2. Raw data message
- {0,1} start: 0xA5 0x5A
- {2} message size: 0x16 (22 bytes)
- {3} message identifier: 0xA2 (Raw)
- {4,5} ACCx: int16
- {6,7} ACCy: int16
- {8,9} ACCz: int16
- {10,11} GYROx: int16
- {12,13} GYROy: int16
- {14,15} GYROz:  int16
- {16,17} Mx: int16
- {18,19} My: int16
- {20,21} Mz: int16
- {22} Checksum: sum all the data apart from the start, and get the lower byte.
- {23} end: 0xAA
