from multiprocessing.dummy import Process
import os
from main import main

def export_secrets_to_env():
    # Lấy nội dung từ biến môi trường ENV_CONFIG (GitHub sẽ nạp từ Secrets vào đây)
    env_config = os.getenv("ENV_CONFIG")
    env_path = ".env"

    if env_config:
        print("[*] Đang phát hiện cấu hình từ GitHub Secrets...")
        try:
            # Ghi đè hoặc tạo mới file .env
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_config.strip())
            print("[+] Đã chuyển đổi ENV_CONFIG sang file .env thành công.")
        except Exception as e:
            print(f"[!] Lỗi khi ghi file .env: {e}")
    else:
        print("[!] Không tìm thấy ENV_CONFIG. Bỏ qua bước tạo file .env (Chế độ Local).")

def run_with_timeout(timeout_seconds):
    # Khởi tạo tiến trình chạy hàm main
    p = Process(target=main)
    p.start()
    
    print(f"[*] Server đã bắt đầu. Thời gian chạy tối đa: {timeout_seconds/3600} giờ.")
    
    # Chờ đợi cho đến khi hết thời gian hoặc tiến trình tự kết thúc
    p.join(timeout=timeout_seconds)

    if p.is_alive():
        print(f"\n[!] Đã hết {timeout_seconds/3600} giờ. Đang dừng server để reset workflow...")
        p.terminate() # Buộc dừng tiến trình
        p.join()
        print("[+] Đã dừng sạch sẽ.")

if __name__ == "__main__":
    export_secrets_to_env()
    main()