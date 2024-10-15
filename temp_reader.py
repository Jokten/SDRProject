import serial
import time
import pmt
import zmq
import numpy as np
import struct


# Set the serial port and baud rate to match your Arduino setup
SERIAL_PORT = '/dev/ttyACM0'  # Replace with your port name, e.g., 'COM3' for Windows, '/dev/ttyUSB0' for Linux
BAUD_RATE = 9600

context = zmq.Context()
socket_zmq = context.socket(zmq.PUB)
socket_zmq.bind("tcp://127.0.0.1:5555")

def float_to_uint8_array(value: float) -> np.ndarray:
    """
    Converts a float to a uint8 NumPy array representing its byte-level representation.

    Parameters:
        value (float): The float value to convert.

    Returns:
        np.ndarray: A NumPy array of type uint8 representing the float.
    """
    # Pack the float into bytes using big-endian double precision
    packed = struct.pack('>d', value)  # Use '<d' for little-endian if needed
    # Convert the bytes to a NumPy array of uint8
    uint8_array = np.frombuffer(packed, dtype=np.uint8)
    return uint8_array

def read_temperature_data():
    try:
        # Open the serial port
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            # Allow time for the connection to initialize
            time.sleep(2)
            
            while True:
                # Read a line of data from the serial port
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    
                    # Print the received data (spoofed temperature)
                    print(f"Received: {line}")
                    line = float(line)
                    pmt_msg = pmt.from_float(line)
                    uint8_array = float_to_uint8_array(line)
                    byte_data = uint8_array.tobytes()
                
                    vec = np.ndarray.tolist(uint8_array)
                    #pmt_msg = pmt.cons(pmt.intern("Temprature"), vec)
                    pmt_msg = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(vec),vec))
                    #pmt_msg = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(5,[0x01,0x02,0x03, 0x04, 0x05]))
                    # Send the PMT message via ZMQ to GNU Radio
                    socket_zmq.send(pmt.serialize_str(pmt_msg))
                    print(f"Sent PMT message via ZMQ: {pmt.to_python(pmt_msg)}")
                
                # Add a delay between reads (optional)
                time.sleep(1)
    
    except serial.SerialException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Reading temperature data from Arduino...")
    read_temperature_data()
