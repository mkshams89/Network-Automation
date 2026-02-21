#!/usr/bin/env python3
"""
Nexus Switch BGP Configuration Script
Connects to a Cisco Nexus switch via SSH and configures BGP neighbor.
"""

import paramiko
import time
import sys
import getpass


def connect_to_switch(ip, username, password):
    """Establish SSH connection to the Nexus switch."""
    print(f"\n[*] Connecting to {ip}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ip,
            username=username,
            password=password,
            timeout=30,
            look_for_keys=False,
            allow_agent=False
        )
        print("[+] Connected successfully!")
        return ssh
    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Please check your credentials.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"[-] SSH error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        sys.exit(1)


def send_command(shell, command, wait=1.5):
    """Send a command to the shell and return output."""
    shell.send(command + "\n")
    time.sleep(wait)
    output = ""
    while shell.recv_ready():
        output += shell.recv(65535).decode("utf-8", errors="ignore")
    return output


def configure_bgp(shell, local_asn, remote_asn, neighbor_ip):
    """Push BGP configuration to the Nexus switch."""
    print("\n[*] Entering configuration mode...")

    commands = [
        ("terminal length 0", 1),
        ("configure terminal", 1),
        (f"feature bgp", 2),
        (f"router bgp {local_asn}", 1),
        (f"neighbor {neighbor_ip} remote-as {remote_asn}", 1),
        (f"neighbor {neighbor_ip} description Configured-via-Script", 1),
        ("end", 1),
    ]

    all_output = ""
    for cmd, wait in commands:
        print(f"    Sending: {cmd}")
        output = send_command(shell, cmd, wait)
        all_output += output
        # Check for common errors
        if "% Invalid" in output or "% Error" in output or "ERROR:" in output:
            print(f"\n[-] Error detected after command '{cmd}':")
            print(output)
            return False, all_output

    print("[+] BGP configuration applied successfully!")
    return True, all_output


def save_configuration(shell):
    """Save the running configuration to startup."""
    print("\n[*] Saving configuration...")
    output = send_command(shell, "copy running-config startup-config", wait=5)
    if "Copy complete" in output or "%" not in output:
        print("[+] Configuration saved successfully!")
    else:
        print("[!] Warning: Configuration may not have saved correctly.")
        print(f"    Output: {output.strip()}")
    return output


def verify_bgp(shell, neighbor_ip):
    """Show BGP neighbor summary for verification."""
    print("\n[*] Verifying BGP configuration...")
    output = send_command(shell, f"show bgp neighbors {neighbor_ip} | include BGP", wait=2)
    if output:
        print("[+] BGP Neighbor Verification Output:")
        print("-" * 40)
        print(output.strip())
        print("-" * 40)


def get_input(prompt, is_password=False):
    """Get user input with optional password masking."""
    if is_password:
        return getpass.getpass(prompt)
    return input(prompt).strip()


def validate_ip(ip):
    """Basic IP address validation."""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def validate_asn(asn):
    """Validate BGP ASN (1-4294967295 for 4-byte ASN)."""
    try:
        asn_int = int(asn)
        return 1 <= asn_int <= 4294967295
    except ValueError:
        return False


def main():
    print("=" * 50)
    print("   Cisco Nexus BGP Configuration Tool")
    print("=" * 50)

    # --- Connection Details ---
    print("\n[Step 1] Switch Connection Details")
    print("-" * 35)

    while True:
        switch_ip = get_input("  Switch IP Address : ")
        if validate_ip(switch_ip):
            break
        print("  [!] Invalid IP address. Please try again.")

    username = get_input("  Username          : ")

    while not username:
        print("  [!] Username cannot be empty.")
        username = get_input("  Username          : ")

    password = get_input("  Password          : ", is_password=True)

    # --- Connect ---
    ssh = connect_to_switch(switch_ip, username, password)
    shell = ssh.invoke_shell()
    time.sleep(2)
    shell.recv(65535)  # Clear the initial banner

    # --- BGP Configuration Details ---
    print("\n[Step 2] BGP Configuration Details")
    print("-" * 35)

    while True:
        local_asn = get_input("  Local BGP ASN     : ")
        if validate_asn(local_asn):
            break
        print("  [!] Invalid ASN. Must be a number between 1 and 4294967295.")

    while True:
        remote_asn = get_input("  Remote BGP ASN    : ")
        if validate_asn(remote_asn):
            break
        print("  [!] Invalid ASN. Must be a number between 1 and 4294967295.")

    while True:
        neighbor_ip = get_input("  Neighbor IP       : ")
        if validate_ip(neighbor_ip):
            break
        print("  [!] Invalid IP address. Please try again.")

    # --- Summary ---
    print("\n[*] Configuration Summary:")
    print(f"    Switch        : {switch_ip}")
    print(f"    Local ASN     : {local_asn}")
    print(f"    Remote ASN    : {remote_asn}")
    print(f"    Neighbor IP   : {neighbor_ip}")

    confirm = get_input("\n  Apply this configuration? (yes/no): ").lower()
    if confirm not in ("yes", "y"):
        print("\n[-] Configuration aborted by user.")
        ssh.close()
        sys.exit(0)

    # --- Apply BGP Config ---
    success, _ = configure_bgp(shell, local_asn, remote_asn, neighbor_ip)

    if not success:
        print("\n[-] Configuration failed. Please review the errors above.")
        ssh.close()
        sys.exit(1)

    # --- Optional: Verify ---
    verify_bgp(shell, neighbor_ip)

    # --- Save Configuration ---
    print("\n[Step 3] Save Configuration")
    print("-" * 35)
    save_confirm = get_input("  Save configuration to startup-config? (yes/no): ").lower()

    if save_confirm in ("yes", "y"):
        save_configuration(shell)
    else:
        print("[!] Configuration NOT saved. Changes will be lost on reboot.")

    # --- Done ---
    ssh.close()
    print("\n[+] Session closed. Done!")
    print("=" * 50)


if __name__ == "__main__":
    main()
