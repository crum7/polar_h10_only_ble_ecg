import asyncio
from bleak import BleakScanner, BleakClient
import numpy as np
import plotly.express as px

# 使用するデバイスの名前
POLAR_H10_NAME = "Polar H10 B91CE12A"  

# ECGデータストリームのUUID
PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])

ecg_session_data = []  # ECGセッションのデータを保存するリスト
ecg_session_time = []  # ECGセッションのタイムスタンプを保存するリスト

#受信したデータの処理
def data_conv(sender, data):
    print("Data received")
    if data[0] == 0x00:
        timestamp = convert_to_unsigned_long(data, 1, 8)
        step = 3
        samples = data[10:]
        offset = 0
        while offset < len(samples):
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            ecg_session_data.extend([ecg])
            ecg_session_time.extend([timestamp])

#指定されたオフセットと長さでデータを符号付き整数に変換
def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=True,
    )

#指定されたオフセットと長さでデータを符号なしの長整数に変換する関数
def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=False,
    )

#メインの非同期関数
async def run():
    devices = await BleakScanner.discover()
    polar_h10_device = None

    # Polar H10デバイスを探す
    for device in devices:
        if device.name and POLAR_H10_NAME in device.name:
            print(f"Polar H10を見つけました: {device}")
            polar_h10_device = device
            break

    if not polar_h10_device:
        print("Polar H10が見つかりませんでした!")
        return

    # Polar H10デバイスとの接続とデータ取得
    async with BleakClient(polar_h10_device) as client:
        await client.connect(timeout=20.0)
        await client.write_gatt_char(PMD_CONTROL, ECG_WRITE)
        await client.start_notify(PMD_DATA, data_conv)
        await asyncio.sleep(10.0)  # 10秒間ECGデータを収集
        await client.stop_notify(PMD_DATA)

        # 収集したECGデータをファイルに保存
        np.savetxt("ecg_session_time.csv", ecg_session_time, delimiter=",")
        np.savetxt("ecg_session_data.csv", ecg_session_data, delimiter=",")
        print("ECGデータ保存")

        # plotlyを使用して、ecgデータを可視化
        fig = px.line(ecg_session_data)
        fig.show()

asyncio.run(run())
