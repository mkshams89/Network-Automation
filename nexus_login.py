from netmiko import ConnectHandler
import getpass

# Prompt user for connection details
print("=" * 40)
print("      Cisco Nexus Switch Login Tool")
print("=" * 40)

host     = input("\nEnter Switch IP Address : ")
username = input("Enter Username          : ")
password = getpass.getpass("Enter Password          : ")

# Define device parameters
nexus_switch = {
    "device_type": "cisco_nxos",
    "host": host,
    "username": username,
    "password": password,
    "port": 22,
}

# Connect to the device
try:
    print(f"\nConnecting to {host}...")
    connection = ConnectHandler(**nexus_switch)

    print("✔ Login successful!\n")

    # Run a basic command to verify connection
    output = connection.send_command("show version")
    print("--- show version ---")
    print(output)

    # Disconnect
    connection.disconnect()
    print("\n✔ Disconnected successfully.")

except Exception as e:
    print(f"\n✘ Connection failed: {e}")
