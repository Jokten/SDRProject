import numpy as np
from gnuradio import gr
import pmt

class add_preamble(gr.basic_block):
    """
    A custom GNU Radio block that prepends a fixed preamble to the input byte data.
    """
    def __init__(self, preamble=[0xAA, 0x55, 0xAA, 0x55]):
        gr.basic_block.__init__(self,
            name="add_preamble",
            in_sig=[np.uint8],   # Input signal is bytes (unsigned 8-bit integers)
            out_sig=[np.uint8])  # Output signal is also bytes

        # Store the preamble as a numpy array of type uint8
        self.preamble = np.array(preamble, dtype=np.uint8)
        # Initialize an index to keep track of preamble transmission
        self.preamble_index = 0
        # Flag to indicate if the preamble has been sent
        self.preamble_sent = True
        self.tag_transmitted = False

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        ninput_items = len(in0)
        noutput_items = len(out)
        #print(ninput_items)
        #print(noutput_items)
        #print("working")

        out_idx = 0  # Output buffer index

        # Process tags in the input items being consumed
        tags = self.get_tags_in_window(0, 0, ninput_items)
        for tag in tags:
            if pmt.equal(tag.key, pmt.intern("start_packet")) and self.preamble_sent and self.tag_transmitted:
                # Determine the position of the tag in the input buffer
                tag_idx = tag.offset - self.nitems_read(0)
                print(f"Found tag at offset {tag.offset}, tag_idx {tag_idx}")
                if 0 <= tag_idx < ninput_items:
                    # Reset preamble state when a new packet starts
                    #print("found packet start")
                    self.preamble_sent = False
                    self.preamble_index = 0
                    # Consume up to the tag position to avoid reprocessing
                    self.consume(0, tag_idx)
                    # Adjust input items after consuming up to tag_idx
                    in0 = in0[tag_idx:]
                    ninput_items = len(in0)
                    break  # Assuming one tag per general_work call

        # Now, decide whether to send the preamble
        if not self.preamble_sent:
            preamble_remaining = len(self.preamble) - self.preamble_index
            output_space = noutput_items

            # Determine how many bytes to copy
            n_to_copy = min(preamble_remaining, output_space, ninput_items)
            out[:n_to_copy] = self.preamble[self.preamble_index:self.preamble_index + n_to_copy]
            self.preamble_index += n_to_copy
            out_idx += n_to_copy

            # print(out)

            # Check if the preamble has been fully sent
            if self.preamble_index == len(self.preamble):
                print("Preambled")
                self.preamble_sent = True
                self.tag_transmitted = False

            self.produce(0, out_idx)
            return gr.WORK_CALLED_PRODUCE  # Return the correct flag

        # After the preamble has been sent, forward the input data
        n_to_copy = min(ninput_items, noutput_items - out_idx)
        out[out_idx:out_idx + n_to_copy] = in0[:n_to_copy]
        out_idx += n_to_copy

        # Consume input items and produce output items
        self.consume(0, n_to_copy)
        self.produce(0, out_idx)
        #print(in0)
        #print(out)
        self.tag_transmitted = True
        return gr.WORK_CALLED_PRODUCE  # Return the correct flag

