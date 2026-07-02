"""
后台启动 RAG 服务（Windows 版）
用法：
  python run_bg.py start   # 后台启动
  python run_bg.py stop    # 停止
  python run_bg.py restart # 重启
  python run_bg.py status  # 查看状态
"""
from typing import Optional
import os
import sys
import signal
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, ".rag_server.pid")
LOG_FILE = os.path.join(BASE_DIR, "server.log")


def get_pid() -> Optional[int]:
    if not os.path.exists(PID_FILE):
        return None
    with open(PID_FILE) as f:
        data = json.load(f)
    return data.get("pid")


def is_running(pid: int) -> bool:
    if pid is None:
        return False
    import ctypes
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    kernel32 = ctypes.windll.kernel32
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid)
    if h:
        kernel32.CloseHandle(h)
        return True
    return False


def start():
    pid = get_pid()
    if pid and is_running(pid):
        print(f"⚠️  服务已在运行（PID {pid}），如需重启请用 restart")
        return

    print(f"🚀 后台启动 RAG 服务，日志写入 {LOG_FILE} ...")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [".venv/Scripts/python.exe", "main.py"],
            cwd=BASE_DIR,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,  # 无窗口后台运行
        )
    with open(PID_FILE, "w") as f:
        json.dump({"pid": proc.pid}, f)
    print(f"✅ 服务已启动（PID {proc.pid}）")
    print(f"   访问地址: http://localhost:8001")
    print(f"   Swagger:  http://localhost:8001/docs")


def stop():
    pid = get_pid()
    if not pid or not is_running(pid):
        print("⚠️  服务未运行")
        # 清理残留 PID 文件
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return
    print(f"🛑 停止服务（PID {pid}）...")
    try:
        os.kill(pid, signal.CTRL_C_EVENT)  # 尝试优雅退出
    except Exception:
        pass
    import time
    for _ in range(10):
        if not is_running(pid):
            break
        time.sleep(0.5)
    else:
        # 强制结束
        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    print("✅ 服务已停止")


def status():
    pid = get_pid()
    if pid and is_running(pid):
        print(f"✅ 服务运行中（PID {pid}）")
        print(f"   访问地址: http://localhost:8001")
    else:
        print("⭕ 服务未运行")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "restart":
        stop()
        import time; time.sleep(1)
        start()
    elif cmd == "status":
        status()
    else:
        print(f"未知命令: {cmd}")
        print("用法: python run_bg.py [start|stop|restart|status]")
