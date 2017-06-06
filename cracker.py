import hashlib
from ecdsa import SECP256k1, SigningKey
import random
import sys
import asyncio
import aiohttp
import time

BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def base58_encode(version, public_address):

    version = bytes.fromhex(version)
    checksum = hashlib.sha256(hashlib.sha256(version + public_address).digest()).digest()[:4]
    payload = version + public_address + checksum
    
    result = int.from_bytes(payload, byteorder="big")

    padding = len(payload) - len(payload.lstrip(b'\0'))
    encoded = []

    while result != 0:
        result, remainder = divmod(result, 58)
        encoded.append(BASE58_ALPHABET[remainder])

    return padding*"1" + "".join(encoded)[::-1]


def get_private_key(hex_string):
    return bytes.fromhex(hex_string.zfill(64))


def get_public_key(private_key):
    return (bytes.fromhex("04") + SigningKey.from_string(private_key, curve=SECP256k1).verifying_key.to_string())


def get_public_address(public_key):
    address = hashlib.sha256(public_key).digest()
    h = hashlib.new('ripemd160')
    h.update(address)
    address = h.digest()
    return address


@asyncio.coroutine
async def fetch_page(address):
    url = "https://blockchain.info/q/addressbalance/" + address[0]
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if(resp.status==200):
                balance = await resp.text()
                if(int(balance)>0):
                    print(address[0] + " Balance: " + balance)
                    with open('./' + address[0] + "_public", 'wb') as f:
                        f.write(address[1])
                    with open('./' + address[0] + "_private", 'wb') as f:
                        f.write(address[2])
                return 1
            return 0


def generate_adresses(n):
    addresses = list()
    for i in range(n):
        n = 64
        alphabet = "0123456789ABCDEF"
        s = ""
        for i in range(n):
            s += random.choice(alphabet)
        try:
            private_key = get_private_key(s)
            public_key = get_public_key(private_key)
            public_address = get_public_address(public_key)
            bitcoin_address = base58_encode("00", public_address)
            addresses.append([bitcoin_address, public_key, private_key])
        except KeyboardInterrupt:
            print("Bye")
            sys.exit()
        except:
            print("Failed to create address " + s)
    return addresses


def main():
    counter =0
    while(True):
        coros = []
        for address in generate_adresses(100):
            coros.append(asyncio.Task(fetch_page(address)))
        for i in (yield from asyncio.gather(*coros)):
            counter+=i
            if(counter%1000==0):
                print("Checked " + str(counter) + " addresses")
        time.sleep(5)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
