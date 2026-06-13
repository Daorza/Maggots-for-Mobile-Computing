import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "12345678-1234-1234-1234-123456789012"
CHAR_UUID    = "87654321-4321-4321-4321-210987654321"
ESP32_NAME   = "ESP32_BLE_LED_KELOMPOK_4"  # ✅ match exact ESP32 name


async def find_esp32():
    print("🔍 Scanning BLE devices...")
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name and ESP32_NAME in d.name:
            print(f"🎯 Found ESP32: {d.address} (name: {d.name})")
            return d.address
    print("❌ ESP32 tidak ditemukan.")
    return None


async def main():
    addr = await find_esp32()
    if not addr:
        return

    async with BleakClient(addr) as client:
        print("🔗 Terhubung ke ESP32.")

        loop = asyncio.get_event_loop()

        while True:
            # ✅ input() runs in thread so BLE stays alive
            cmd = await loop.run_in_executor(None, lambda: input("Perintah (ON/OFF/exit): ").strip().upper())

            if cmd == "EXIT":
                break
            elif cmd in ("ON", "OFF"):
                await client.write_gatt_char(CHAR_UUID, cmd.encode("utf-8"), response=True)
                print("📤 Perintah dikirim:", cmd)

                value = await client.read_gatt_char(CHAR_UUID)
                print("📥 Dari ESP32:", value.decode("utf-8", errors="ignore"))
            else:
                print("Perintah salah. Gunakan: ON/OFF/exit.")

        print("👋 Disconnecting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram berhenti.")