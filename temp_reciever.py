import time
import pmt
import zmq
import numpy as np
import struct

# Set the ZMQ connection details
ZMQ_ADDRESS = "tcp://127.0.0.1:5554"  # The address to connect to (should match the publisher)
ZMQ_TOPIC = ""  # Empty string means subscribe to all topics

def uint8_array_to_float(uint8_array: bytes) -> float:
    """
    Converts a byte array back to a float.

    Parameters:
        uint8_array (bytes): The byte array representing the float.

    Returns:
        float: The decoded float value.
    """
    # Ensure that the byte array is the correct length for a double precision float
    if len(uint8_array) != 8:
        uint8_array = uint8_array[:8]
        #raise ValueError(f"Invalid byte array length for float conversion: {len(uint8_array)} bytes")

    # Unpack the bytes into a float using big-endian double precision
    value = struct.unpack('>d', uint8_array)[0]  # Use '<d' for little-endian if needed
    return value

def decode_pmt_message(pmt_msg):
    """
    Decodes a PMT message to extract the float temperature.

    Parameters:
        pmt_msg: The PMT message received.

    Returns:
        float: The decoded temperature value, or None if decoding fails.
    """
    print(pmt.is_u8vector(pmt_msg))
    dr = pmt.cdr(pmt_msg)
    data = bytes(pmt.u8vector_elements(dr))
    # Extract the second part of the pair, which should be the u8vector

    
    # Check if it's a u8vector

    # Get the length and data from the u8vector

    # Debug: Print the raw byte data
    print(f"Raw byte data received: {data.hex()}")

    try:
        # Convert the byte data back to float
        temperature = uint8_array_to_float(data)
        return temperature
    except struct.error as e:
        print(f"Error unpacking float from byte data: {e}")
        return None
    except ValueError as ve:
        print(f"Value error: {ve}")
        return None

def receive_temperature_data():
    # Initialize ZMQ context and subscriber socket
    context = zmq.Context()
    socket_zmq = context.socket(zmq.SUB)
    socket_zmq.connect(ZMQ_ADDRESS)
    socket_zmq.setsockopt_string(zmq.SUBSCRIBE, ZMQ_TOPIC)  # Subscribe to all topics

    print(f"Connected to ZMQ publisher at {ZMQ_ADDRESS}. Waiting for temperature data...")

    try:
        while True:
            # Receive a serialized PMT message
            serialized_msg = socket_zmq.recv()

            # Deserialize the PMT message
            pmt_msg = pmt.deserialize_str(serialized_msg)

            # Decode the PMT message to get the temperature
            temperature = decode_pmt_message(pmt_msg)

            if temperature is not None:
                print(f"Received Temperature: {temperature} °C")
            else:
                print("Failed to decode temperature from PMT message.")

            # Optional: Add a short delay to prevent tight loop
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")

    finally:
        socket_zmq.close()
        context.term()

if __name__ == "__main__":
    receive_temperature_data()
