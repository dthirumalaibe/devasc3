#!/usr/bin/env python

"""
Author: Nick Russo
Purpose: Using NETCONF with Openconfig YANG models to manage Ethernet
VLANs on a Cisco NX-OS switch via the always-on Cisco DevNet sandbox.
"""


import xmltodict
from lxml.etree import fromstring
from ncclient import manager
from ncclient.operations import RaiseMode


def main():
    """
    Execution begins here.
    """

    # Dictionary containing keyword arguments (kwargs) for connecting
    # via NETCONF. Because SSH is the underlying transport, there are
    # several minor options to set up.
    connect_params = {
        "host": "sbx-nxos-mgmt.cisco.com",
        "port": 10000,
        "username": "admin",
        "password": "Admin_1234!",
        "hostkey_verify": False,
        "allow_agent": False,
        "look_for_keys": False,
        "device_params": {"name": "nexus"},
    }

    # Unpack the connect_params dict and use them to connect inside
    # of a "with" context manager. The variable "conn" represents the
    # NETCONF connection to the device.
    with manager.connect(**connect_params) as conn:
        print("NETCONF session connected")

        # To save time, only capture 3 switchports. Less specific filters
        # will return more information, but take longer to process/transport.
        nc_filter = """
            <interfaces xmlns="http://openconfig.net/yang/interfaces">
                <interface>
                    <name>eth1/71</name>
                </interface>
                <interface>
                    <name>eth1/72</name>
                </interface>
                <interface>
                    <name>eth1/73</name>
                </interface>
            </interfaces>
        """

        # Execute a "get-config" RPC using the filter defined above
        resp = conn.get_config(source="running", filter=("subtree", nc_filter))

        # Uncomment line below to see raw RPC XML reply; great for learning
        # print(resp.xml)

        # Parse the XML text into a Python dictionary
        jresp = xmltodict.parse(resp.xml)

        # Uncomment line below to see parsed JSON RPC; great for learning
        # import json; print(json.dumps(jresp, indent=4))

        # Iterate over all the interfaces returned by get-config
        for intf in jresp["rpc-reply"]["data"]["interfaces"]["interface"]:

            # Declare a few local variables to make accessing data deep
            # within the JSON structure a little easier
            config = intf["ethernet"]["switched-vlan"]["config"]
            mode = config["interface-mode"].lower()

            # Print common switchport data
            print(f"Name: {intf['name']:<7}  Type: {mode:<6}", end="  ")

            # Print additional data depending on access vs trunk ports
            if mode == "access":
                print(f"Access VLAN: {config['access-vlan']}")
            elif mode == "trunk":
                print(f"Native VLAN: {config['native-vlan']}")
            else:
                print(f"(no additional data)")

        # Define the VLAN and interface to be updated
        # Challenge for viewers: enhance it to take a collections of VLANs
        # instead of just one at a time!
        intf = "eth1/73"
        vlan = 333
        trunk = True

        # Perform the update, and if success, print a message
        config_resp = update_vlan(conn, intf, vlan, trunk)
        if config_resp.ok:
            print(f"{intf} VLAN updated to {vlan}")

            # Save config, and if success, print a message
            save_resp = save_config_nxos(conn)

            if save_resp.ok:
                print("Successfully saved config")

    print("NETCONF session disconnected")


def update_vlan(conn, intf_name, vlan_id, trunk=False):
    """
    Updates an existing switchport with a new VLAN ID. Expects that the
    NETCONF connection is already open and that all data is valid. Feel
    free to add more data validation here as a challenge.
    """

    # Prepare the arguments. If trunk is true, then we will change the port
    # type to be a trunk and update the native-vlan. Otherwise, its an access
    # port and we will update the access-vlan.
    if trunk:
        intf_mode = "TRUNK"
        vlan_type = "native-vlan"
    else:
        intf_mode = "ACCESS"
        vlan_type = "access-vlan"

    # NETCONF edit-config RPC payload which defines interface to update.
    # This follows the YANG model we picked apart in the get-config section.
    intf_to_update = {
        "name": intf_name,
        "ethernet": {
            "@xmlns": "http://openconfig.net/yang/interfaces/ethernet",
            "switched-vlan": {
                "@xmlns": "http://openconfig.net/yang/vlan",
                "config": {
                    vlan_type: str(vlan_id),
                    "interface-mode": intf_mode,
                },
            },
        },
    }

    # Assemble correct payload structure containing interface list, along
    # with any other items to be updated
    config_dict = {
        "config": {  # also "data"
            "interfaces": {
                "@xmlns": "http://openconfig.net/yang/interfaces",
                "interface": [intf_to_update],
            }
        }
    }

    # Assemble the XML payload by "unparsing" the JSON dict, then
    # issue an edit-config RPC to the NX-OS device. Return the
    # rpc-reply so that the caller can take action on the result.
    xpayload = xmltodict.unparse(config_dict)

    # Secure a "lock" to prevent other NETCONF clients from configuring
    # the system concurrently. The lock is released automatically after
    # the "with" context ends.
    with conn.locked("candidate"):

        # We could change the "running" datastore directly, but using
        # the "candidate" option gives us the option to discard changes.
        # By changing the RaiseMode to NONE, we tell ncclient not to raise
        # errors, but instead to pass along the rpc-error. We change it
        # back to ALL after this RPC call so future RPCs will raise errors.
        conn.raise_mode = RaiseMode.NONE
        config_resp = conn.edit_config(target="candidate", config=xpayload)
        conn.raise_mode = RaiseMode.ALL
        if config_resp.ok:
            # We need to "commit" from "candidate" to "running" config, an
            # intermediate step not needed if we editted "running" directly.
            conn.commit()
            print("Changes committed from candidate to running config")
        else:
            # Something went wrong, print the error. In a real environment,
            # there might have been valid configuration applied already,
            # so discarding any pending changes might be a safe approach.
            print(f"Failed to apply config. Error: {config_resp.error}")
            conn.discard_changes()
            print("Changes discarded")

    return config_resp


def save_config_nxos(conn):
    """
    Save config on Cisco NX-OS is complex and requires a custom RPC.
    Reference the NX-OS programmability documentation for further details.
    """

    save_rpc = """
        <copy_running_config_src xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
             <startup-config/>
        </copy_running_config_src>
    """
    save_resp = conn.dispatch(fromstring(save_rpc))
    return save_resp


if __name__ == "__main__":
    main()
