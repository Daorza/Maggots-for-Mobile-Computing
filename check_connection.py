"""
check_connection.py
Cek apakah broker MQTT maggot bisa dijangkau dari komputer kamu.
Tidak perlu install apa pun selain paho-mqtt.

Jalankan:
    pip install paho-mqtt
    python check_connection.py
"""

import socket
import ssl
import time
import json
import threading

BROKER   = "hayasaka.takofaru.dpdns.org"
PORT     = 8883
USERNAME = "web_maggot"
PASSWORD = "NJkyX*L47EEpzzFd@1W#fIf@"
TIMEOUT  = 10   # detik

results = {}

# ─────────────────────────────────────────────────────────────────
# 1. DNS Resolution
# ─────────────────────────────────────────────────────────────────
def check_dns():
    print("\n[1/4] DNS Resolution...")
    try:
        ip = socket.gethostbyname(BROKER)
        results["dns"] = {"ok": True, "ip": ip}
        print(f"  ✅ OK  →  {BROKER}  =  {ip}")
    except socket.gaierror as e:
        results["dns"] = {"ok": False, "error": str(e)}
        print(f"  ❌ GAGAL  →  {e}")
        print("     Kemungkinan: domain salah, atau DNS kamu tidak resolve domain ini.")

# ─────────────────────────────────────────────────────────────────
# 2. TCP Port Reachability
# ─────────────────────────────────────────────────────────────────
def check_tcp():
    print("\n[2/4] TCP Port 8883...")
    try:
        sock = socket.create_connection((BROKER, PORT), timeout=TIMEOUT)
        sock.close()
        results["tcp"] = {"ok": True}
        print(f"  ✅ OK  →  Port {PORT} terbuka")
    except socket.timeout:
        results["tcp"] = {"ok": False, "error": "timeout"}
        print(f"  ❌ TIMEOUT  →  Port {PORT} tidak merespons dalam {TIMEOUT}s")
        print("     Kemungkinan: firewall memblokir port 8883.")
    except ConnectionRefusedError:
        results["tcp"] = {"ok": False, "error": "refused"}
        print(f"  ❌ REFUSED  →  Port {PORT} ditolak")
        print("     Kemungkinan: broker tidak berjalan di port ini.")
    except Exception as e:
        results["tcp"] = {"ok": False, "error": str(e)}
        print(f"  ❌ ERROR  →  {e}")

# ─────────────────────────────────────────────────────────────────
# 3. TLS Handshake + Sertifikat
# ─────────────────────────────────────────────────────────────────
def check_tls():
    print("\n[3/4] TLS Handshake & Sertifikat...")
    if not results.get("tcp", {}).get("ok"):
        print("  ⏭️  Dilewati (TCP gagal)")
        return
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((BROKER, PORT), timeout=TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=BROKER) as tls:
                cert = tls.getpeercert()
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer  = dict(x[0] for x in cert.get("issuer",  []))
                expiry  = cert.get("notAfter", "?")
                results["tls"] = {"ok": True, "subject": subject, "issuer": issuer, "expiry": expiry}
                print(f"  ✅ OK  →  TLS握手 berhasil")
                print(f"     CN      : {subject.get('commonName', '?')}")
                print(f"     Issuer  : {issuer.get('organizationName', '?')}")
                print(f"     Expired : {expiry}")
    except ssl.SSLCertVerificationError as e:
        results["tls"] = {"ok": False, "error": str(e)}
        print(f"  ❌ SERTIFIKAT TIDAK VALID  →  {e}")
        print("     Kemungkinan: sertifikat self-signed atau expired.")
    except Exception as e:
        results["tls"] = {"ok": False, "error": str(e)}
        print(f"  ❌ TLS ERROR  →  {e}")

# ─────────────────────────────────────────────────────────────────
# 4. MQTT Auth + Subscribe (tes full koneksi)
# ─────────────────────────────────────────────────────────────────
def check_mqtt():
    print("\n[4/4] MQTT Auth & Subscribe...")
    if not results.get("tls", {}).get("ok"):
        print("  ⏭️  Dilewati (TLS gagal)")
        return

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("  ⚠️  paho-mqtt belum terinstall. Jalankan: pip install paho-mqtt")
        return

    done  = threading.Event()
    error = []

    def on_connect(client, userdata, flags, reason_code, properties=None):
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        if rc == 0:
            results["mqtt"] = {"ok": True}
            print("  ✅ OK  →  Autentikasi berhasil")
            print(f"     User    : {USERNAME}")
            print(f"     Broker  : {BROKER}:{PORT}")
            # subscribe cek
            client.subscribe("maggot/sensor/data")
            client.subscribe("maggot/status/fase")
            print("  ✅ Subscribe berhasil ke:")
            print("       • maggot/sensor/data")
            print("       • maggot/status/fase")
        else:
            codes = {
                1: "bad protocol version",
                2: "client id rejected",
                3: "server unavailable",
                4: "bad credentials (username/password salah)",
                5: "not authorized",
            }
            msg = codes.get(rc, f"unknown rc={rc}")
            error.append(msg)
            results["mqtt"] = {"ok": False, "error": msg}
            print(f"  ❌ AUTH GAGAL  →  {msg}")
        done.set()

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        print(f"\n  📨 Pesan masuk dari [{msg.topic}]:")
        try:
            data = json.loads(payload)
            print(f"     JSON: {json.dumps(data, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"     Text: {payload}")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="maggot-checker",
        clean_session=True,
    )
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, keepalive=30)
        client.loop_start()
        done.wait(timeout=TIMEOUT)
        # tunggu sebentar kalau ada pesan masuk
        if results.get("mqtt", {}).get("ok"):
            print("\n  ⏳ Menunggu pesan 5 detik (tekan Ctrl+C untuk stop)...")
            time.sleep(5)
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        results["mqtt"] = {"ok": False, "error": str(e)}
        print(f"  ❌ CONNECT ERROR  →  {e}")


# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
def print_summary():
    print("\n" + "═" * 50)
    print("  RINGKASAN HASIL CEK")
    print("═" * 50)
    checks = [
        ("DNS",  results.get("dns",  {}).get("ok")),
        ("TCP",  results.get("tcp",  {}).get("ok")),
        ("TLS",  results.get("tls",  {}).get("ok")),
        ("MQTT", results.get("mqtt", {}).get("ok")),
    ]
    all_ok = True
    for name, ok in checks:
        if ok is True:
            print(f"  ✅  {name}")
        elif ok is False:
            print(f"  ❌  {name}")
            all_ok = False
        else:
            print(f"  ⏭️  {name}  (dilewati)")
            all_ok = False

    print("═" * 50)
    if all_ok:
        print("  🎉  SEMUA OK — dashboard siap dijalankan!")
    else:
        print("  ⚠️  Ada masalah koneksi — lihat detail di atas.")
    print()


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("═" * 50)
    print("  MQTT Broker Connection Checker")
    print(f"  Target: {BROKER}:{PORT}")
    print("═" * 50)

    check_dns()
    check_tcp()
    check_tls()
    check_mqtt()
    print_summary()