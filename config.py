# config.py

PROXMOX_HOST = "192.168.1.123"
PROXMOX_USER = "root@pam"
PROXMOX_TOKEN_ID = "Token_Name"
PROXMOX_TOKEN_SECRET = "Token_Secret"
VERIFY_SSL = False

# List of VMs to manage
VM_IDS = [100, 101, 102, 103]

# If True, show confirmation dialog before sending actions
SHY = True

# List of lists of VMs that share the same resources (e.g., GPU)
# When one VM from a group is running, others in the same group will be hidden
# Example: [[101, 102], [103, 104]] means VMs 101&102 share resources, and 103&104 share resources. You can add as many groups as you like.
SAME_RESOURCES = [
    [101, 102],  
    [103, 104]   
]
