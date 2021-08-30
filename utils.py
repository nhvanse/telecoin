import re

def is_valid_address(address):
    check = re.match("^0x[a-fA-F0-9]{40}$", address)
    
    return bool(check)

def format_number(number):
    if number < 1:
        result = round(number, 3)
    else:
        result = round(number, 2)
        if (result == int(result)):
            result = int(result)
            
        result = f'{result:,}'

    return str(result)