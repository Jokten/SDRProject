import numpy as np
from gnuradio import gr
import pmt

class add_packet_start_tag(gr.sync_block):
    """
    A custom GNU Radio sync block that adds a "packet_start" tag
    at the start of each packet, using the "packet_len" tag to determine packet length.
    """
    def __init__(self, packet_len_tag_key="packet_len"):
        gr.sync_block.__init__(self,
            name="add_packet_start_tag",
            in_sig=[np.uint8],    # Input signal (bytes)
            out_sig=[np.uint8])   # Output signal (bytes)

        # Store the tag key for packet length
        self.packet_len_tag_key = pmt.intern(packet_len_tag_key)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        # Copy input data to output buffer
        noutput_items = len(out)
        out[:] = in0[:noutput_items]

        # Retrieve tags that represent packet boundaries (with packet lengths)
        tags = self.get_tags_in_window(0, 0, noutput_items)
        
        for tag in tags:
            # Check if the tag is the packet length tag
            if pmt.equal(tag.key, self.packet_len_tag_key):
                # Convert the tag value from PMT to a Python integer
                packet_len = pmt.to_long(tag.value)
                #print("found tag")
                #print(packet_len)
                if packet_len > 0:
                    # Get the start of the packet (where the tag is located)
                    packet_start = tag.offset - self.nitems_written(0)
                    #print("Added tag")
                    # Ensure the packet start is within the current output buffer
                    if 0 <= packet_start < noutput_items:
                        # Add a "packet_start" tag at the beginning of the packet
                        self.add_item_tag(0,                # Output port index
                                          self.nitems_written(0) + packet_start,  # Tag position in the stream
                                          pmt.intern("start_packet"),             # Tag key
                                          pmt.PMT_NIL)                            # Tag value (optional)

        return noutput_items

