import asyncio
from bleak import BleakClient

ESP32_ADDRESS = "dc:da:0c:5a:03:e5"
CHARACTERISTIC_UUID = "abcd1234-5678-1234-5678-abcdef123456"

async def read_test_data():
    async with BleakClient(ESP32_ADDRESS) as client:
        if await client.is_connected():
            print("Connected to ESP32")

            def notification_handler(sender, data):
                message = data.decode("utf-8")
                print(f"Received: {message}")

            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            await asyncio.sleep(10)
            await client.stop_notify(CHARACTERISTIC_UUID)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(read_test_data())
