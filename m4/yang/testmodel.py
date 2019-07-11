#!/usr/bin/env python

"""
Author: Nick Russo
Purpose: Consume pyangbind Python object-oriented bindings to
interact with custom YANG model. Inspired by David Barroso:
https://napalm-automation.net/yang-for-dummies/
"""

import json
import interfaces

def main():
    """
    Execution begins here.
    """
    module = interfaces.interfaces()

    eth01 = module.interface_container.switchport_list.add("Ethernet0/1")
    eth01.enabled = True
    eth01.vlan = 11

    eth02 = module.interface_container.switchport_list.add("Ethernet0/2")
    eth02.enabled = True
    eth02.vlan = 22

    eth03 = module.interface_container.switchport_list.add("Ethernet0/3")
    try:
        print("Trying to set a bogus VLAN")
        eth03.vlan = 9999
    except ValueError as exc:
        print(exc.args[0]["error-string"])

    lb0 = module.interface_container.virtual_list.add("Loopback0")
    lb0.enabled = True
    lb0.ip_address = "192.0.2.1"

    lb1 = module.interface_container.virtual_list.add("Loopback1")

    print(json.dumps(module.get(), indent=2))


if __name__ == "__main__":
    main()
