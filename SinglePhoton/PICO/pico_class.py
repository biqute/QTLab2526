import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, mV2adc, assert_pico_ok
import time
import sys
import os

sys.path.append(r"C:\Users\kid\labQT\Lab2025\Single photon")

from QTLab2526.SinglePhoton.PICO.instruments import Instrument
import threading
import json
import atexit

#C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\PICO

class PicoScope(Instrument):
    """
    Interface for controlling PicoScope 5000 series oscilloscopes.
    
    This class provides methods to configure and control PicoScope oscilloscopes,
    including channel setup, triggering, and data acquisition.
    """
    def __init__(self, name: str = None):
        name = name if name else "PicoScope_no_ID"
        super().__init__(name)
        
        # No resolution parameter needed, 8-bit resolution by default for PS5000
        self.resolution = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_8BIT']
        
        # Handle for device
        self.chandle = ctypes.c_int16()
        
        # Set up channel information storage
        self.channel_info = {}
        
        # Register the kill method to be called at exit
        atexit.register(self.kill)

    def set_channel(self, channel, enabled, coupling, range, offset):
        """
        Configure a channel on the oscilloscope.
        
        Parameters
        ----------
        channel : str
            Channel identifier ('A', 'B', 'C', 'D')
        enabled : bool
            Whether to enable the channel
        coupling : str
            Channel coupling type ('DC' or 'AC')
        range : str
            Channel voltage range in volts (e.g., '2V') or millivolts (e.g., '20MV')
        offset : float
            Channel offset in volts
        """
        enabled = 1 if enabled else 0
        status_key = f"setCh{channel}"
        
        try:
            range_value = ps.PS5000A_RANGE[self.get_command_value('RANGE', range)]
        except KeyError:
            raise ValueError(f"Invalid range: {range}. Check the available ranges on the json file.")
        
        self.status[status_key] = ps.ps5000SetChannel(self.chandle,
                                                    ps.PS5000A_CHANNEL[f'PS5000A_CHANNEL_{channel}'],
                                                    enabled,
                                                    ps.PS5000A_COUPLING['PS5000A_DC' if coupling == 'DC' else 'PS5000A_AC'],
                                                    range_value,
                                                    offset)
        assert_pico_ok(self.status[status_key])

        # Store the channel information
        self.channel_info[channel] = {'enabled': enabled, 'coupling': coupling, 'range': range_value, 'offset': offset}

    def acq_block(self, sample_rate: float, post_trigger_samples: int, pre_trigger_samples: int = 0, memory_segment_index: int = 0, time_out: int = 3000):
        """
        Acquire a block of data from the oscilloscope.
        
        Parameters
        ----------
        sample_rate : float
            The desired sampling rate in Hz
        post_trigger_samples : int
            The number of samples to acquire after the trigger event
        pre_trigger_samples : int, optional
            The number of samples to acquire before the trigger event (default: 0)
        memory_segment_index : int, optional
            The index of the memory segment to use (default: 0)
        time_out : int, optional
            The timeout in milliseconds (default: 3000)
            
        Returns
        -------
        dict
            Dictionary containing the acquired data (in mV) for each channel and the time data
            
        Raises
        ------
        TimeoutError
            If the acquisition times out
        """
        no_of_samples = pre_trigger_samples + post_trigger_samples
        if no_of_samples == 0:
            raise Warning("No samples to acquire. Set pre_trigger_samples or post_trigger_samples. 100 samples will be acquired.")
            no_of_samples = 100
        
        # Get timebase for the given sample rate
        timebase = self.calculate_timebase(sample_rate)
        
        # Hanldlers for returned values
        timeIndisposedMs = ctypes.c_int32()
        pParameter = ctypes.c_void_p()
        
        # Run the block acquisition
        self.status["runBlock"] = ps.ps5000RunBlock(
            self.chandle,
            pre_trigger_samples,
            post_trigger_samples,
            timebase,
            ctypes.byref(timeIndisposedMs),
            memory_segment_index,
            None,
            ctypes.byref(pParameter)
        )
        assert_pico_ok(self.status["runBlock"])
        
        # Check for data collection to finish using ps5000IsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        start_time = time.time() # Set a timeout for the acquisition
        while ready.value == check.value:
            self.status["isReady"] = ps.ps5000IsReady(self.chandle, ctypes.byref(ready))
            if time.time() - start_time > time_out / 1000:  # Convert milliseconds to seconds
                raise TimeoutError("Block acquisition timed out.")
               
        assert_pico_ok(self.status["isReady"])
        
        # Calculate the number of samples to be collected
        buffers = {}
        for ch in self.channel_info.keys():
            if self.channel_info[ch]['enabled']:
                buffers[ch] = {'Max': (ctypes.c_int16 * no_of_samples)(), 'Min': (ctypes.c_int16 * no_of_samples)()}
            
        # Set data buffer location for data collection from active channels
        for ch in buffers.keys():
            source = ps.PS5000A_CHANNEL[f"PS5000A_CHANNEL_{ch}"]
            status_key = f"setDataBuffers{ch}"
            self.status[status_key] = ps.ps5000SetDataBuffers(
                self.chandle,
                source,
                ctypes.byref(buffers[ch]['Max']),
                ctypes.byref(buffers[ch]['Min']),
                no_of_samples,
                memory_segment_index,
                0  # No downsampling for block mode
            )
            assert_pico_ok(self.status[status_key])
        
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(no_of_samples)
        
        self.status["getValues"] = ps.ps5000GetValues(self.chandle, 0, ctypes.byref(cmaxSamples), 1, 0, memory_segment_index, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])
        if overflow.value != 0:
            print(f"Overflow occurred: {overflow.value} samples lost.")
            self.status["overflow"] = overflow.value
        
        # convert ADC counts data to mV
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps5000MaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])
        
        data = {}
        for ch in buffers.keys():
            data[ch] =  adc2mV(buffers[ch]['Max'], self.channel_info[ch]['range'], maxADC)

        # Create time data
        data['time'] = np.linspace(0, (cmaxSamples.value - 1) / sample_rate, cmaxSamples.value)
        
        return data

    def acq_streaming(self, sample_rate: float = 4e6, buffer_size: int = 500):
        """
        Start streaming data acquisition continuously.
        
        Parameters
        ----------
        sample_rate : float, optional
            The desired sampling rate in Hz (default: 4e6, or 4 MHz)
        buffer_size : int, optional
            Size of the buffer for data acquisition (default: 500)
        """
        self._streaming_stop = False
        self._streamed_data = []  # reset storage
        self._buffer_size = buffer_size
        
        # Convert sample_rate to sample_interval in ns
        sample_interval = int(1e9 / sample_rate)
        
        # Create a buffer for channel A (for simplicity, one channel is used)
        self._bufferA = np.zeros(shape=buffer_size, dtype=np.int16)

        # Register the data buffer with the driver for channel A
        status_key = "setDataBufferA_stream"
        self.status[status_key] = ps.ps5000SetDataBuffer(self.chandle,
                                                        ps.PS5000A_CHANNEL['PS5000A_CHANNEL_A'],
                                                        self._bufferA.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                        buffer_size,
                                                        0,
                                                        0)
        assert_pico_ok(self.status[status_key])

        # Streaming mode: no pretrigger, no autoStop (0 means continuous)
        maxPreTriggerSamples = 0
        autoStopOn = 0  # continuous streaming
        downsampleRatio = 1
        
        # Start streaming
        sample_interval_ct = ctypes.c_int32(sample_interval)
        self.status["runStreaming_stream"] = ps.ps5000RunStreaming(self.chandle,
                                                                   ctypes.byref(sample_interval_ct),
                                                                   0,  # time units
                                                                   maxPreTriggerSamples,
                                                                   0,  # total samples
                                                                   autoStopOn,
                                                                   downsampleRatio,
                                                                   0,  # no downsampling
                                                                   buffer_size)
        assert_pico_ok(self.status["runStreaming_stream"])

        # Define callback function for streaming
        def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
            if noOfSamples > 0:
                chunk = self._bufferA[startIndex:startIndex+noOfSamples].copy()
                self._streamed_data.append(chunk)
            return 0

        cFuncPtr = ps.StreamingReadyType(streaming_callback)

        def streaming_thread():
            while not self._streaming_stop:
                self.status["getStreaming"] = ps.ps5000GetStreamingLatestValues(self.chandle, cFuncPtr, None)
                time.sleep(0.01)
            # Stop streaming
            self.status["stop_stream"] = ps.ps5000Stop(self.chandle)
            assert_pico_ok(self.status["stop_stream"])
            print("Streaming stopped.")

        # Start streaming thread
        self._streaming_thread = threading.Thread(target=streaming_thread)
        self._streaming_thread.start()

    def stop_streaming(self):
        """
        Stop streaming data acquisition.
        """
        self._streaming_stop = True
        if self._streaming_thread is not None:
            self._streaming_thread.join()

    def get_streamed_data(self):
        """
        Get the acquired streaming data.
        """
        if self._streamed_data:
            return np.concatenate(self._streamed_data)
        else:
            return np.array([], dtype=np.int16)
        
    def calculate_timebase(self, sampling_rate: float) -> int:
        """
        Calculate the oscilloscope timebase value for a given sampling rate.
        """
        # Timebase calculation for PS5000 series
        return int(np.round(1e9 / sampling_rate))

    def initialize(self):
        """
        Initialize the connection to the device.
        """
        # Open the PicoScope device
        self.status["openunit"] = ps.ps5000OpenUnit(ctypes.byref(self.chandle), None)
        assert_pico_ok(self.status["openunit"])

        # Disable all channels
        self.disable_all_channels()

    def disable_all_channels(self):
        """
        Disable all input channels (A, B, C, D).
        """
        for channel in ['A', 'B', 'C', 'D']:
            self.set_channel(channel, False, 'DC', '20MV', 0)

    def kill(self):
        """
        Stop the oscilloscope and close the connection.
        """
        # Stop the scope
        self.status["stop"] = ps.ps5000Stop(self.chandle)
        assert_pico_ok(self.status["stop"])

        # Close the connection
        self.status["close"] = ps.ps5000CloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

    def info(self):
        """
        Display status information about the device.
        """
        print(self.status)

    
    def __del__(self):
        """
        Destructor to ensure the connection is closed when the object is deleted.
        """
        # Ensure the connection is closed when the object is deleted
        if self.status['close'] == None and self.status['stop'] == None :
            self.close_connection()