# Module 6 - Deploying RESTCONF for Lightweight Network Management
This directory contains HTTP GET and HTTP POST RESTCONF examples to
collect and update DHCP pool configurations on Cisco IOS-XE, respectively.

## Scripts
The `make_trees.sh` script leverages `pyang` to build tree representations
of the YANG models relevant for the course.

## Demo prep
For this demo, the following DHCP pool is already configured on
the sandbox, which can be added using the `add_pools.py` script or
manually via CLI.
```
ip dhcp pool GLOBOMANTICS_VLAN10
 network 192.0.2.0 255.255.255.0
 default-router 192.0.2.254
 dns-server 8.8.8.8 8.8.4.4
 domain-name globomantics.com
```

## Data References
The `data_ref/` directory contains the following reference data:
  * Raw XML RPC-reply payload from `get-config`
  * Parsed JSON RPC-reply payload from `get-config`
  * `pyang` text tree representation of the relevant
    OpenConfig models used in this module
