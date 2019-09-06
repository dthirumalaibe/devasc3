#!/usr/bin/env python

import json
from pyats import aetest
from genie.conf import Genie


class NetworkTestcase(aetest.Testcase):

    @aetest.setup
    def setup(self):
        # Store variable for quick access to device list
        self.devices = self.parameters["testbed"].devices

        # Connect to all devices in the tested at once
        self.parameters["testbed"].connect()

    @aetest.test
    def test_ospf_neighbors(self):
        for name, device in self.devices.items():
            nbrs = json.dumps(device.parse("show ip ospf neighbor"), indent=2)
            print(f"{name} OSPF neighbors:\n{nbrs}")


if __name__ == "__main__":
    testbed = Genie.init("testbed.yml")
    aetest.main(testbed=testbed)
