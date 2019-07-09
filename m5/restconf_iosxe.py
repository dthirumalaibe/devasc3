#!/usr/bin/env python


"""
Author: Nick Russo
Purpose: Using RESTCONF with IOS-XE specific YANG models to manage DHCP
server pools on a Cisco OS-XE router via the always-on Cisco DevNet sandbox.
"""

import json
import requests


def main():
    """
    Execution begins here.
    """

    # The IOS-XE sandbox uses a self-signed cert at present, so let's ignore any
    # obvious security warnings for now.
    requests.packages.urllib3.disable_warnings()

    # The API path below is what the DevNet sandbox uses for API testing,
    # which may change in the future. Be sure to check the IP address as
    # I suspect this changes frequently. See here for more details:
    # https://developer.cisco.com/site/ios-xe
    api_path = "https://ios-xe-mgmt.cisco.com:9443/restconf"
    dhcp_target = "data/Cisco-IOS-XE-native:native/ip/dhcp"

    auth = ("root", "D_Vay!_10&")
    get_headers = {"Accept": "application/yang-data+json"}
    post_headers = {
        "Content-Type": "application/yang-data+json",
        "Accept": "application/yang-data+json, application/yang-data.errors+json",
    }

    # Issue a GET request to collect a list of network objects configured
    # on FTD. These are the IP subnets, hosts, and FQDNs that might be
    # included in various security access policies.
    get_dhcp_response = requests.get(
        f"{api_path}/{dhcp_target}",
        headers=get_headers,
        auth=auth,
        verify=False,
    )
    if get_dhcp_response.ok and get_dhcp_response.text:
        dhcp_pools = get_dhcp_response.json()["Cisco-IOS-XE-native:dhcp"]
        for pool in dhcp_pools["Cisco-IOS-XE-dhcp:pool"]:
            print(f"ID: {pool['id']}")
            print(f"  Domain: {pool['domain-name']}")
            print(f"  Network: {pool['network']['number']}")
            print(f"  Netmask: {pool['network']['mask']}")
            print(f"  Default gateways:")
            for defgate in pool["default-router"]["default-router-list"]:
                print(f"    {defgate}")
            print(f"  DNS servers:")
            for dns in pool["dns-server"]["dns-server-list"]:
                print(f"    {dns}")
    else:
        print("No DHCP pools currently configured")

    add_pool = {
        "Cisco-IOS-XE-dhcp:pool": [
            {
                "id": "NICKTEST",
                "default-router": {"default-router-list": ["192.0.2.254"]},
                "dns-server": {"dns-server-list": ["8.8.4.4", "8.8.8.8"]},
                "domain-name": "njrusmc.net",
                "network": {"number": "192.0.2.0", "mask": "255.255.255.0"},
            }
        ]
    }

    post_dhcp_response = requests.post(
        f"{api_path}/{dhcp_target}",
        headers=post_headers,
        auth=auth,
        data=json.dumps(add_pool),
        verify=False,
    )
    if post_dhcp_response.status_code == 201:
        print("Created new DHCP pool via RESTCONF")
        post_save_response = requests.post(
            f"{api_path}/operations/cisco-ia:save-config",
            headers=post_headers,
            auth=auth,
            verify=False,
        )
        if post_save_response.status_code == 200:
            print("Saved configuration")


if __name__ == "__main__":
    main()
