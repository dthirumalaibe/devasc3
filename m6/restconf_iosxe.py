#!/usr/bin/env python


"""
Author: Nick Russo
Purpose: Using RESTCONF with IOS-XE specific YANG models to manage DHCP
server pools on a Cisco IOS-XE router via the always-on Cisco DevNet sandbox.
"""

import json
import requests


def main():
    """
    Execution begins here.
    """

    # The IOS-XE sandbox uses a self-signed cert at present, so let's
    # ignore any obvious security warnings for now.
    requests.packages.urllib3.disable_warnings()

    # The API path below is what the DevNet sandbox uses for API testing,
    # which may change in the future. Be sure to check the IP address as
    # I suspect this changes frequently. See here for more details:
    # https://developer.cisco.com/site/ios-xe
    api_path = "https://ios-xe-mgmt.cisco.com:9443/restconf"

    # The specific path to update DHCP configuration per YANG model.
    # You can explore using Postman/curl or through the YANG model directly.
    dhcp_target = "data/Cisco-IOS-XE-native:native/ip/dhcp"

    # Create 2-tuple for "basic" authentication using Cisco DevNet credentials.
    # No fancy tokens needed to get basic RESTCONF working on Cisco IOS-XE.
    auth = ("root", "D_Vay!_10&")

    # Define headers for issuing HTTP GET requests to receive YANG data as JSON.
    get_headers = {"Accept": "application/yang-data+json"}

    # Issue a GET request to collect the DHCP pool information only. This will
    # return a list of dictionaries where each dictionary represents a pool.
    get_dhcp_response = requests.get(
        f"{api_path}/{dhcp_target}/pool",
        headers=get_headers,
        auth=auth,
        verify=False,
    )

    # Uncomment the line below to see the JSON response; great for learning
    print(json.dumps(get_dhcp_response.json(), indent=2))

    # If the request succeed with a 200 "OK" message and there is
    # some text defined, then step through the JSON and extract the useful
    # bits of information. This is a good exercise to work on accessing data
    # from complex JSON structure.
    if get_dhcp_response.status_code == 200 and get_dhcp_response.text:
        dhcp_pools = get_dhcp_response.json()["Cisco-IOS-XE-dhcp:pool"]

        for pool in dhcp_pools:
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

    # Create JSON structure to add a new pool along with the HTTP POST
    # headers needed to add it. The JSON below represents this
    # configuration:
    # ip dhcp pool NICKTEST
    #  network 192.0.2.0 255.255.255.0
    #  default-router 192.0.2.254
    #  dns-server 8.8.8.8 8.8.4.4
    #  domain-name njrusmc.net
    add_pool = {
        "Cisco-IOS-XE-dhcp:pool": [
            {
                "id": "test3",
                "default-router": {"default-router-list": ["198.51.100.44"]},
                "dns-server": {"dns-server-list": ["8.8.4.4", "8.8.8.8"]},
                "domain-name": "njrusmc.net",
                "network": {"number": "198.51.100.0", "mask": "255.255.255.0"},
            }
        ]
    }
    post_headers = {
        "Content-Type": "application/yang-data+json",
        "Accept": "application/yang-data+json, application/yang-data.errors+json",
    }

    # Issue HTTP POST request to a similar URL used for the GET request,
    # except carrying the new DHCP pool in the HTTP body. Also, we don't need
    # to specify "/pool" since the dictionary key in the body carries it.
    post_dhcp_response = requests.post(
        f"{api_path}/{dhcp_target}",
        headers=post_headers,
        auth=auth,
        data=json.dumps(add_pool),
        verify=False,
    )

    # Uncomment the line below to see the JSON response; great for learning
    # print(json.dumps(post_dhcp_response.json(), indent=4))

    # HTTP 201 means "created", implying a new resource was added. The
    # response will tell us the URL of the newly-created resource, simplifying
    # future removal.
    if post_dhcp_response.status_code == 201:
        print(f"Added DHCP pool at: {post_dhcp_response.headers['Location']}")
        print(json.dumps(add_pool, indent=2))

        # Save configuration whenever the DHCP pool is added. This ensures
        # the configuration will persist across reboots.
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
