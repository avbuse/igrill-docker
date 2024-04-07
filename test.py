import asyncio
from bleak import BleakScanner

async def scan_and_connect():
    scanner = BleakScanner()
    devices = await scanner.discover()

    for device in devices:
        print(f"Checking device: {device.name}")
        if "iGrill" in device.name:
            print(f"Found iGrill device: {device}")
            # Connect to the device (this doesn't actually pair the device in the Bluetooth sense)
            # The following line is a placeholder, as the python bleak library does not support pairing
            # You might need to use a different library or tool to pair the devices
            print("Pairing is not supported in this script.")
            return

loop = asyncio.get_event_loop()
loop.run_until_complete(scan_and_connect())