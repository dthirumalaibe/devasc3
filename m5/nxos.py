from ncclient import manager
import xmltodict
import json


def main():

    with manager.connect(
        host="sbx-nxos-mgmt.cisco.com",
        port=10000,
        username="admin",
        password="Admin_1234!",
        hostkey_verify=False,
        device_params={"name": "nexus"},
        timeout=60,
    ) as conn:
        resp = conn.get_config(
            source="running",
            filter=(
                "subtree",
                '<interfaces xmlns="http://openconfig.net/yang/interfaces"></interfaces>',
            ),
        )
        jresp = xmltodict.parse(resp.xml)
        print(json.dumps(jresp, indent=2))

        # this mess needs cleanup, but basically prints all switchport
        # info for access and trunk ports. no SVI or L3 ports
        for intf in jresp["rpc-reply"]["data"]["interfaces"]["interface"]:
            switchport = intf.get("ethernet")
            if switchport:
                switched_vlan = switchport.get("switched-vlan")
                if switched_vlan:
                    eth = switched_vlan["config"]
                    mode = eth["interface-mode"].lower()
                    print(f"Name: {intf['name']:<8}  Type: {mode:<6}", end="  ")

                    if mode == "access":
                        print(f"Access VLAN: {eth['access-vlan']}")
                    elif mode == "trunk":
                        print(f"Native VLAN: {eth['native-vlan']}")
                    else:
                        print(f"(no additional data)")


def update_vlan(intf_name, vlan_id):
    intf_to_update = {
        "name": intf_name,
        "ethernet": {
            "@xmlns": "http://openconfig.net/yang/interfaces/ethernet",
            "switched-vlan": {
                "@xmlns": "http://openconfig.net/yang/vlan",
                "config": {"access-vlan": str(vlan_id)},
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

    xpayload = xmltodict.unparse(config_dict)
    with manager.connect(
        host="sbx-nxos-mgmt.cisco.com",
        port=10000,
        username="admin",
        password="Admin_1234!",
        hostkey_verify=False,
        device_params={"name": "nexus"},
    ) as conn:
        config_resp = conn.edit_config(target="running", config=xpayload)
    print(f"{intf_name} VLAN updated to {vlan_id}")


if __name__ == "__main__":
    update_vlan("eth1/124", 518)
    main()
