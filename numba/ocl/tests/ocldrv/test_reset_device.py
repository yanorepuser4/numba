from __future__ import print_function, absolute_import, division
import threading
from numba import ocl
import unittest

class TestResetDevice(unittest.TestCase):
    def test_reset_device(self):

        def newthread():
            devices = range(len(ocl.list_devices()))
            print('Devices', devices)
            for _ in range(2):
                for d in devices:
                    ocl.select_device(d)
                    print('Selected device', d)
                    ocl.close()
                    print('Closed device', d)

        # Do test on a separate thread so that we don't affect
        # the current context in the main thread.
        t = threading.Thread(target=newthread)
        t.start()
        t.join()


if __name__ == '__main__':
    unittest.main()
