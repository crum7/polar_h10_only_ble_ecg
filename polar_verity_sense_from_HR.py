import asyncio
from bleak import BleakScanner, BleakClient
import re
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 使用するデバイスの名前 :  DEVICEIDを変更
POLAR_VERITY_SENSE_NAME = "Polar Sense"
# HeartRateを呼び出すcharacteristic
HR_CHARACTERISTIC_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

def parse_heart_rate_measurement(data):
  # 最初のバイトはフラグフィールド
    if data[0] == 0x00:
        # 2番目のバイトが心拍数の値
        heart_rate = data[1]
        print(f"Heart Rate: {heart_rate} bpm")
    else:
        print("Received data format is not recognized.")
    return heart_rate



def notification_handler(sender, data):
    print(f"Received data from {sender}: {data}")
    heart_rate = parse_heart_rate_measurement(data)
    print(f"Heart Rate: {heart_rate} bpm")



async def run(name):
    devices = await BleakScanner.discover()
    polar_verity_sense_device = None
    #デバイスと接続
    for device in devices:
        if device.name and name in device.name:
            logger.info(f"Polar Verity Sense found: {device}")
            polar_verity_sense_device = device
            break
    if not polar_verity_sense_device:
        logger.error("Polar Verity Sense not found.")
        return


    async with BleakClient(polar_verity_sense_device) as client:
        if client.is_connected:
            print("Connected to the device")

            try:
                #notifyをスタート
                await client.start_notify(HR_CHARACTERISTIC_UUID, notification_handler)
                print(f"Subscribed to {HR_CHARACTERISTIC_UUID}")
            except Exception as e:
                print(f"Could not subscribe to {HR_CHARACTERISTIC_UUID}: {e}")
                
            print("Subscribed to all possible characteristics. Listening for notifications...")
            await asyncio.sleep(60)

            try:
                await client.stop_notify(HR_CHARACTERISTIC_UUID)
                print(f"Unsubscribed from {HR_CHARACTERISTIC_UUID}")
            except Exception as e:
                print(f"Could not unsubscribe from {HR_CHARACTERISTIC_UUID}: {e}")
        else:
            print("Failed to connect.")

asyncio.run(run(POLAR_VERITY_SENSE_NAME))






