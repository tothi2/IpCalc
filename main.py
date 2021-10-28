from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

# I used metadata to give a name and description to each of my endpoints.
tags_metadata = [
    {
        "name": "IpCalc",
        "description": "This endpoint takes in a JSON request, and will return the following:"
                       "The class of the address, number of networks, number of hosts and the first and last address.",
    },
    {
        "name": "Subnets",
        "description": "This endpoint takes in a Class B or C address and a subnet mask."
                       "The ip in CIDR, The number of subnets, number of addressable hosts, valid subnets, broadcast addresses and valid hosts on each subnet.",
    },
    {
        "name": "Supernets",
        "description": "This endpoint takes in a list of class C addresses which become a supernet, the endpoint returns the CIDR notation and the network mask",
    },
]

# I implement my app as FastAPI and make sure to use my metadata here.
app = FastAPI(
    openapi_tags=tags_metadata,
    title="IpCalculator"
)


# The following list of classes are the classes I made for each point, each also have a working example.
class IpCalc(BaseModel):
    address: str = Field(..., title="any IP Address", example="136.206.18.7") 

class Subnet(BaseModel):
    address: str = Field(..., example="192.168.10.0")
    mask: str = Field(..., example="255.255.255.192")

class Supernet(BaseModel):
    addresses: list = Field(..., example=["205.100.0.0","205.100.1.0","205.100.2.0","205.100.3.0"])


# Here i actually define the endpoints as post requests
@app.post("/ipcalc", tags=["IpCalc"])
async def ipcalc(ipcalc: IpCalc):
    ipsplit = ipcalc.address.split(".")
    return calculations(ipsplit)

@app.post("/subnet", tags=["Subnets"])
async def subnets(subnet: Subnet):
    masksplit = subnet.mask.split(".")
    ip = subnet.address.split(".")
    return subnetting(masksplit, ip)

@app.post("/supernet", tags=["Supernets"])
async def supernets(supernet: Supernet):
    superip = supernet.addresses
    return supernetting(superip)


# The third endpoint is responsible for super netting, the following function was meant for that but this was the one part I struggled with.
# I understand what supernetting is and what it does, but I really struggled to implement it for any length list of Class C IP addresses.
def supernetting(superip):
    i = 0
    l = []
    while i < len(superip):
        l.append(superip[i].split("."))
        i += 1
    

    binarystring = ""
    j = 0
    binaryip = []
    while j < len(l):
        binaryip.append('{0:08b} {1:08b} {2:08b} {3:08b}'.format(int(l[j][0]),int(l[j][1]),int(l[j][2]),int(l[j][3]))) #very ugly way I found to convert the IP to binary
        j += 1
    
    bitcount = 0
    bitlist = 0
    bitstring = ""
    binarysupernet = ""
    if binaryip[0][27:35] and binaryip[(len(binaryip) - 1)][27:35] == "00000000":  # My painful attempt starts here, at finding how many bits need to deducted from 32 in order to find the "cut off" point in the supernet ip and supernet mask.
        bitcount = bitcount + 8
        if binaryip[0][18:26] and binaryip[(len(binaryip) - 1)][18:26] == "00000000":
            bitcount = bitcount + 8
        else:
            bitlist = bitlist + int(binaryip[0][18:26]) + int(binaryip[(len(binaryip) - 1)][18:26])
            bitstring = len(str(bitlist))
            bitcount = bitcount + bitstring
            cidr = 0
            cidr = 32 - bitcount
            i = 0
            while i < (32 - bitcount):
                binarysupernet = binarysupernet + "1"
                i += 1

            
            i = 0
            while i < bitcount:
                binarysupernet = binarysupernet + "0"
                i += 1

            binarysupernet = '.'.join(binarysupernet[i:i+8] for i in range(0, len(binarysupernet), 8))
            binarysupernet = binarysupernet.split(".")
            supernetmask = ""
            i = 0
            while i < len(binarysupernet):
                supernetmask = supernetmask + str(int((binarysupernet[i]),2)) + "."
                i += 1
            supernetmask = supernetmask[:len(supernetmask) - 1]
    finaladdress = ""
    testaddress = binaryip[0].replace(" ","")
    testaddress = testaddress[:-bitcount]
    testaddress = testaddress + ("0" * bitcount)
    testaddress = " ".join(testaddress[i:i+8] for i in range(0, len(testaddress), 8))
    testaddress = testaddress.split()
    i = 0
    while i < len(testaddress):
        finaladdress = finaladdress + str(int((testaddress[i]),2)) + "."
        i += 1
    finaladdress = finaladdress[:len(finaladdress) - 1]
    
    
    return{
        "address": finaladdress + "/" + str(cidr),
        "mask": supernetmask
    }



# The second endpoint required the user to input an ip and a subnet mask, this function then calculates the CIDR, number of subnets, addressable hosts per subnet, valid subnets, broadcast addresses, first addresses and last addresses.
def subnetting(masksplit, ip):
    numsubs = 0 
    s = []
    s.append('{0:08b}.{1:08b}.{2:08b}.{3:08b}'.format(int(masksplit[0]),int(masksplit[1]),int(masksplit[2]),int(masksplit[3]))) # It might be ugly but it gets the job done.
    s = ".".join(s)
    numhosts = s.count("0")
    numhosts = 2 ** numhosts - 2
    singles = s.split(".")
    for element in singles:
        if str(element) == "11111111":
            pass
        elif int(element) == 0:
            pass
        elif int(element) > 0:
            numsubs = element.count("1")
            numsubs = 2 ** numsubs
    
    cidr = s.count("1")
    finalip = ".".join(ip)

    # It was only after writing all the following code that I realized there was definitely a shorter way of reorganizing the ip over and over again, but I found that this way still works.


    
    # Class B Subnetting
    if(int(ip[0]) >=128 and int(ip[0]) <= 191):
        broadcast_address = []
        if masksplit[2] == "0" and masksplit [3] == "0":
            valid_subnets = []
        
        elif masksplit[2] == "255" and masksplit [3] == "0":
            valid_subnets = []
        
        elif masksplit[2] == "255" and masksplit[3] == "255":
            valid_subnets = []
            numhosts = 0

        elif masksplit[3] == "0":
            last_address = []
            first_address = []
            broadcast_address = []
            valid_subnets = []
            valid_digits = []
            intvalid_digits = []
            valid_digits.append(str(0))
            digit = 256 - int(masksplit[2])
            block = 0
            i = 0
            while i < (numsubs):
                laststring = ""
                firststring = ""
                validstring = ""
                broadcaststring = ""
                block = block + digit
                intvalid_digits.append(block)
                valid_digits.append(str(block))
                firststring = firststring + ip[0] + "." + ip[1] + "." + valid_digits[i] + "." + "1"
                validstring = validstring + ip[0] + "." + ip[1] + "." + valid_digits[i] + "." + ip[3]
                broadcaststring = broadcaststring + ip[0] + "." + ip[1] + "." + str((intvalid_digits[i]) - 1) + "." + "255"
                laststring = laststring + ip[0] + "." + ip[1] + "." + str((intvalid_digits[i]) - 1) + "." + "254"
                valid_subnets.append(validstring)
                first_address.append(firststring)
                broadcast_address.append(broadcaststring)
                last_address.append(laststring)
                i += 1

        elif masksplit[3] != "0":
            last_address = []
            first_address = []
            broadcast_address = []
            valid_subnets = []
            valid_digits = []
            intvalid_digits = []
            intvalid_digits.append(0)
            valid_digits.append(str(0))
            digit = 256 - int(masksplit[3])
            block = 0
            i = 0
            while i < numsubs:
                laststring = ""
                firststring = ""
                validstring = ""
                broadcaststring = ""
                block = block + digit
                intvalid_digits.append(block)
                valid_digits.append(str(block))
                firststring = firststring + ip[0] + "." + ip[1] + "." + ip[2] + "." + str((intvalid_digits[i]) + 1)
                validstring = validstring + ip[0] + "." + ip[1] + "." + ip[2] + "." + valid_digits[i]
                broadcaststring = broadcaststring + ip[0] + "." + ip[1] + "." + ip[2] + "." + str((intvalid_digits[i + 1]) - 1)
                laststring = laststring + ip[0] + "." + ip[1] + "." + ip[2] +  "." + str((intvalid_digits[i + 1]) - 2)
                broadcast_address.append(broadcaststring)
                valid_subnets.append(validstring)
                first_address.append(firststring)
                last_address.append(laststring)
                i += 1




    # Class C Subnetting

    if(int(ip[0]) >= 192 and int(ip[0]) <= 223):
        if masksplit[3] == "255":
            valid_subnets = []
            numhosts = 0
        elif masksplit [3] == "0":
            valid_subnets = []
        else:
            last_address = []
            first_address = []
            broadcast_address = []
            valid_subnets = []
            valid_digits = []
            intvalid_digits = []
            intvalid_digits.append(0)
            valid_digits.append(str(0))
            digit = 256 - int(masksplit[3])
            block = 0
            i = 0
            while i < (numsubs):
                    laststring = ""
                    firststring = ""
                    validstring = ""
                    broadcaststring = ""
                    block = block + digit
                    intvalid_digits.append(block)
                    valid_digits.append(str(block))
                    firststring = firststring + ip[0] + "." + ip[1] + "." + ip[2] + "." + str((intvalid_digits[i]) + 1)
                    validstring = validstring + ip[0] + "." + ip[1] + "." + ip[2] + "." + valid_digits[i]
                    broadcaststring = broadcaststring + ip[0] + "." + ip[1] + "." + ip[2] + "." + str((intvalid_digits[i + 1]) - 1)
                    laststring = laststring + ip[0] + "." + ip[1] + "." + ip[2] +  "." + str((intvalid_digits[i + 1]) - 2)
                    valid_subnets.append(validstring)
                    broadcast_address.append(broadcaststring)
                    first_address.append(firststring)
                    last_address.append(laststring)
                    i += 1
            


    return {
        "address_cidr": finalip + "/" + str(cidr),
        "num_subnets": numsubs,
        "addressable_hosts_per_subnet": numhosts,
        "valid_subnets": valid_subnets,
        "broadcast_addresses": broadcast_address,
        "first_addresses": first_address,
        "last_addresses": last_address
    }


# The first endpoint takes an input of an ip address and returns what class that IP is, the number of networks for that class, number of hosts, the first address of the class and the last address of the class.

def calculations(ipsplit):

    if(int(ipsplit[0]) >= 0 and int(ipsplit[0]) <= 127):
        return {
            "class": "A",
            "num_networks": 127,
            "num_hosts": 16777214,
            "first_address": "0.0.0.0",
            "last_address": "127.255.255.255"
    }
   
    elif(int(ipsplit[0]) >=128 and int(ipsplit[0]) <= 191):
        return {
            "class": "B",
            "num_networks": 16384,
            "num_hosts": 65536,
            "first_address": "128.0.0.0",
            "last_address": "191.255.255.255"
    }
   
    elif(int(ipsplit[0]) >= 192 and int(ipsplit[0]) <= 223):
        return {
            "class": "C",
            "num_networks": 2097152,
            "num_hosts": 254,
            "first_address": "192.0.0.0",
            "last_address": "223.255.255.255"
    }
   
    elif(int(ipsplit[0]) >= 224 and int(ipsplit[0]) <= 239):
        return {
            "class": "D",
            "num_networks": "N/A",
            "num_hosts": "N/A",
            "first_address": "224.0.0.0",
            "last_address": "239.255.255.255"
    }
   
    else:
        return {
            "class": "E",
            "num_networks": "N/A",
            "num_hosts": "N/A",
            "first_address": "240.0.0.0",
            "last_address": "255.255.255.255"
    }

