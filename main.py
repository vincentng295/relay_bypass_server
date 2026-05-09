import os
import json
from dotenv import load_dotenv
import threading
import subprocess
import platform
import uuid

def main():
    # =========================================
    # CONFIG SERVER FRP (Thay đổi thông tin ở đây)
    # =========================================

    # XRAY CONFIG
    def init_env_file():
        env_path = ".env"
        # Các giá trị mặc định
        default_configs = {
            "PORT": "8888",
            "XRAY_UUID": str(uuid.uuid4()),
            "DEST_SNI": "m.tiktok.com",
            "PRIVATE_KEY": "sD7SQLbL_Ka6U2Fyu2tMxWAfz5ZFn093LF0ihwl9n24",
            "PUBLIC_KEY": "3u34YvqYDL3DtKfCPWPH9HjEYjnWv1xitfGErFRhDR8",
            "SHORT_ID": "6baad05fed",
            "FRP_SERVER_ADDR": "frp.freefrp.net",
            "FRP_SERVER_PORT": "7000",
            "FRP_TOKEN": "freefrp.net",
            "REMOTE_PORT": "12345"
        }

        if not os.path.exists(env_path):
            print("[*] File .env không tồn tại. Đang tạo file với cấu hình mặc định...")
            with open(env_path, "w", encoding="utf-8") as f:
                for key, value in default_configs.items():
                    f.write(f"{key}={value}\n")
            print("[+] Đã tạo file .env thành công.")
        else:
            print("[*] Đã tìm thấy file .env.")

    # 1. Khởi tạo file .env nếu chưa có
    init_env_file()

    # 2. Load các biến vào môi trường
    load_dotenv()

    # 3. Đọc biến từ môi trường (ưu tiên biến hệ thống/GitHub Secrets, sau đó mới đến .env)
    PORT = int(os.getenv("PORT", 8888))
    UUID = os.getenv("XRAY_UUID", str(uuid.uuid4()))
    DEST_SNI = os.getenv("DEST_SNI", "m.tiktok.com")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY", "sD7SQLbL_Ka6U2Fyu2tMxWAfz5ZFn093LF0ihwl9n24")
    PUBLIC_KEY = os.getenv("PUBLIC_KEY", "3u34YvqYDL3DtKfCPWPH9HjEYjnWv1xitfGErFRhDR8")
    SHORT_ID = os.getenv("SHORT_ID", "6baad05fed")
    FRP_SERVER_ADDR = os.getenv("FRP_SERVER_ADDR", "frp.freefrp.net")
    FRP_SERVER_PORT = int(os.getenv("FRP_SERVER_PORT", 7000))
    FRP_TOKEN = os.getenv("FRP_TOKEN", "freefrp.net")
    REMOTE_PORT = int(os.getenv("REMOTE_PORT", 12345))

    print(f"[*] Kết nối đến FRP: {FRP_SERVER_ADDR}:{REMOTE_PORT}")

    XRAY_BIN = "./xray.exe" if platform.system().lower() == "windows" else "./xray"
    FRPC_BIN = "./frpc.exe" if platform.system().lower() == "windows" else "./frpc"

    # =========================================
    # TẠO FILE CẤU HÌNH
    # =========================================
    def write_configs():
        # 1. Cấu hình Xray (VLESS Reality)
        xray_config = {
            "log": {"loglevel": "error"},
            "inbounds": [{
                "listen": "127.0.0.1",
                "port": PORT,
                "protocol": "vless",
                "settings": {"clients": [{"id": UUID, "flow": "xtls-rprx-vision"}], "decryption": "none"},
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "show": False, "dest": f"{DEST_SNI}:443", "xver": 0,
                        "serverNames": [DEST_SNI], "privateKey": PRIVATE_KEY,
                        "shortIds": [SHORT_ID], "fingerprint": "chrome"
                    }
                }
            }],
            "outbounds": [{"protocol": "freedom", "settings": {"domainStrategy": "UseIP"}}]
        }
        with open("config.json", "w") as f: json.dump(xray_config, f, indent=2)

        # 2. Cấu hình Frp (frpc.toml)
        frp_toml = f"""
    serverAddr = "{FRP_SERVER_ADDR}"
    serverPort = {FRP_SERVER_PORT}
    auth.token = "{FRP_TOKEN}"

    [[proxies]]
    name = "vless-reality-{UUID[:6]}"
    type = "tcp"
    localIP = "127.0.0.1"
    localPort = {PORT}
    remotePort = {REMOTE_PORT}
    """
        with open("frpc.toml", "w") as f: f.write(frp_toml)

    # =========================================
    # CHẠY DỊCH VỤ (Cập nhật để hiện Log)
    # =========================================
    def log_reader(pipe, prefix):
        """Hàm đọc log từ pipe và in ra màn hình"""
        try:
            with pipe:
                for line in iter(pipe.readline, ''):
                    print(f"[{prefix}] {line.strip()}")
        except Exception:
            pass

    def start_services():
        write_configs()
        
        # Khởi chạy Xray
        xp = subprocess.Popen(
            [XRAY_BIN, "run", "-c", "config.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Khởi chạy Frp
        fp = subprocess.Popen(
            [FRPC_BIN, "-c", "frpc.toml"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Chạy các luồng đọc log song song
        threading.Thread(target=log_reader, args=(xp.stdout, "XRAY"), daemon=True).start()
        threading.Thread(target=log_reader, args=(fp.stdout, "FRP"), daemon=True).start()

        return xp, fp

    # In link URI trước
    vless_uri = (
        f"vless://{UUID}@{FRP_SERVER_ADDR}:{REMOTE_PORT}"
        f"?security=reality&sni={DEST_SNI}&fp=chrome"
        f"&pbk={PUBLIC_KEY}&sid={SHORT_ID}&type=tcp&flow=xtls-rprx-vision"
        f"#FRP_Reality"
    )
    print("\n" + "="*60)
    print(f"URI: {vless_uri}")
    print("="*60 + "\n")

    file = "frp_info.config"
    with open(file, "w") as f:
        f.write(vless_uri)

    xp, fp = start_services()

    try:
        # Giữ script chạy để xem log
        fp.wait()
    except KeyboardInterrupt:
        print("\n[*] Đang dừng dịch vụ...")
        xp.terminate()
        fp.terminate()

if __name__ == "__main__":
    main()