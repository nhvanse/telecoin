import re

def is_valid_address(address):
    check = re.match("^0x[a-fA-F0-9]{40}$", address)
    
    return bool(check)