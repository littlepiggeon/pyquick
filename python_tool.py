import tkinter as tk
from tkinter import ttk, filedialog,messagebox
import subprocess
import os
import threading
import requests
import sv_ttk
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings()

# 获取当前工作目录
MY_PATH = os.getcwd()

# 如果保存目录不存在，则创建它
SAVED_DIR = os.path.join(MY_PATH, "saved")
if not os.path.exists(SAVED_DIR):
    os.mkdir(SAVED_DIR)

# 可供选择的 Python 版本列表
VERSIONS = [
    "3.11.0",
    "3.10.0",
    "3.9.0",
    "3.8.0",
    "3.7.0",
    "3.6.0",
    "3.5.0"
]

# 全局变量
file_size = 0
executor = None
futures = []
lock = threading.Lock()
downloaded_bytes = [0]
is_downloading = False

def clear():
    """清除状态标签和包标签的文本"""
    status_label.config(text="")
    package_label.config(text="Enter Package Name:")

def select_destination():
    """选择目标路径"""
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)

def validate_version(version):
    """验证版本号格式"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))

def validate_path(path):
    """验证路径是否存在"""
    return os.path.isdir(path)

def download_chunk(url, start_byte, end_byte, destination, retries=3):
    """下载文件的指定部分"""
    global is_downloading
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            with lock:
                with open(destination, 'r+b') as f:
                    f.seek(start_byte)
                    for chunk in response.iter_content(chunk_size=8192):
                        if not is_downloading:
                            return False
                        f.write(chunk)
                        downloaded_bytes[0] += len(chunk)
            return True
        except requests.RequestException as e:
            with lock:
                status_label.config(text=f"Download Failed! Retrying... ({attempt + 1}/{retries})")
            attempt += 1
    with lock:
        status_label.config(text=f"Download Failed! Error: {str(e)}")
        is_downloading = False
    return False


def download_file(selected_version, destination_path, num_threads):
    """下载指定版本的Python安装程序"""
    global file_size, executor, futures, downloaded_bytes, is_downloading
    if not validate_version(selected_version):
        status_label.config(text="Invalid version number")
        root.after(5000, clear)
        return

    if not validate_path(destination_path):
        status_label.config(text="Invalid destination path")
        root.after(5000, clear)
        return

    file_name = f"python-{selected_version}-amd64.exe"
    destination = os.path.join(destination_path, file_name)

    if os.path.exists(destination):
        try:
            os.remove(destination)
        except (PermissionError, FileNotFoundError) as e:
            status_label.config(text=f"Failed to remove existing file: {str(e)}")
            root.after(5000, clear)
            return

    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-amd64.exe"

    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        file_size = int(response.headers['Content-Length'])
    except requests.RequestException as e:
        status_label.config(text=f"Failed to get file size: {str(e)}")
        root.after(5000, clear)
        return

    try:
        with open(destination, 'wb') as f:
            pass
    except IOError as e:
        status_label.config(text=f"Failed to create file: {str(e)}")
        root.after(5000, clear)
        return

    chunk_size = file_size // num_threads
    futures = []
    downloaded_bytes = [0]
    is_downloading = True

    executor = ThreadPoolExecutor(max_workers=num_threads)
    for i in range(num_threads):
        start_byte = i * chunk_size
        end_byte = start_byte + chunk_size - 1 if i != num_threads - 1 else file_size - 1
        futures.append(executor.submit(download_chunk, url, start_byte, end_byte, destination))

    threading.Thread(target=update_progress, daemon=True).start()
    cancel_button.config(state="normal")  # 启用取消下载按钮

def update_progress():
    """更新进度条和状态标签"""
    global file_size, is_downloading
    while any(not future.done() for future in futures):
        if not is_downloading:
            break
        progress = int(downloaded_bytes[0] / file_size * 100)
        downloaded_mb = downloaded_bytes[0] / (1024 * 1024)
        total_mb = file_size / (1024 * 1024)
        status_label.config(text=f"Progress: {progress}% ({downloaded_mb:.2f} MB / {total_mb:.2f} MB)")
        progress_bar['value'] = progress
        time.sleep(0.1)
    if is_downloading:
        status_label.config(text="Download Complete!")
    else:
        status_label.config(text="Download Cancelled!")
    is_downloading = False
    cancel_button.config(state="disabled")  # 禁用取消下载按钮

def cancel_download():
    """取消正在进行的下载"""
    global is_downloading
    is_downloading = False
    if executor:
        executor.shutdown(wait=False)
    cancel_button.config(state="disabled")  # 禁用取消下载按钮


def download_selected_version():
    """开始下载选定的Python版本"""
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    num_threads = int(thread_combobox.get())

    if not os.path.exists(destination_path):
        status_label.config(text="Invalid path!")
        root.after(5000, clear)
        return

    threading.Thread(target=download_file, args=(selected_version, destination_path, num_threads), daemon=True).start()



def confirm_cancel_download():
    """确认取消下载"""
    if messagebox.askyesno("Confirm", "Are you sure you want to cancel the download?"):
        cancel_download()

def get_pip_version():
    """获取当前pip版本"""
    try:
        return subprocess.check_output(["pip", "--version"], creationflags=subprocess.CREATE_NO_WINDOW).decode().strip().split()[1]
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        return None

def get_latest_pip_version():
    """获取最新pip版本"""
    try:
        r = requests.get("https://pypi.org/pypi/pip/json", verify=False)
        return r.json()["info"]["version"]
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def update_pip():
    """更新pip到最新版本"""
    try:
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        return False

def check_pip_version():
    """检查并更新pip版本"""
    current_version = get_pip_version()
    if current_version is None:
        package_label.config(text="Error: Failed to get current pip version")
        time.sleep(5)
        clear()
        return

    latest_version = get_latest_pip_version()
    if latest_version is None:
        package_label.config(text="Error: Failed to get latest pip version")
        time.sleep(5)
        clear()
        return

    if current_version != latest_version:
        message = f"Current pip version: {current_version}\nLatest pip version: {latest_version}\nUpdating pip..."
        package_label.config(text=message)
        if update_pip():
            package_label.config(text=f"pip has been updated! {latest_version}")
            time.sleep(5)
            clear()
        else:
            package_label.config(text="Error: Failed to update pip")
            time.sleep(5)
            clear()
    else:
        package_label.config(text=f"pip is up to date: {current_version}")
        time.sleep(5)
        clear()

def upgrade_pip():
    """启动pip版本检查线程"""
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(target=check_pip_version, daemon=True).start()
    except FileNotFoundError:
        package_label.config(text="Python is not installed.")
        time.sleep(5)
        clear()
    except Exception as e:
        package_label.config(text=f"Error: {str(e)}")
        time.sleep(5)
        clear()

def install_package():
    """安装指定的Python包"""
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()

        def install_package_thread():
            try:
                result = subprocess.run(["python", "-m", "pip", "install", package_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                installed = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if "Successfully installed" in result.stdout:
                    package_label.config(text=f"Package '{package_name}' has been installed successfully!")
                    time.sleep(5)
                    clear()
                elif package_name.lower() in installed.lower():
                    package_label.config(text=f"Package {package_name} is already installed.")
                    time.sleep(5)
                    clear()
                else:
                    package_label.config(text=f"Error installing package '{package_name}': {result.stderr}")
                    time.sleep(5)
                    clear()
            except Exception as e:
                package_label.config(text=f"Error installing package '{package_name}': {str(e)}")
                time.sleep(5)
                clear()

        threading.Thread(target=install_package_thread).start()
    except FileNotFoundError:
        package_label.config(text="Python is not installed.")
        time.sleep(5)
        clear()
    except Exception as e:
        package_label.config(text=f"Error: {str(e)}")
        time.sleep(5)
        clear()

def uninstall_package():
    """卸载指定的Python包"""
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()

        try:
            installed_packages = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python", "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if "Successfully uninstalled" in result.stdout:
                    package_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                    time.sleep(5)
                    clear()
                else:
                    package_label.config(text=f"Error uninstalling package '{package_name}': {result.stderr}")
                    time.sleep(5)
                    clear()
            else:
                package_label.config(text=f"Package '{package_name}' is not installed.")
                time.sleep(5)
                clear()
        except Exception as e:
            package_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
            time.sleep(5)
            clear()
    except FileNotFoundError:
        package_label.config(text="Python is not installed.")
        time.sleep(5)
        clear()
    except Exception as e:
        package_label.config(text=f"Error: {str(e)}")
        time.sleep(5)
        clear()

def check_python_installation():
    """检查Python是否已安装"""
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        status_label.config(text="Python is not installed.")
        pip_upgrade_button.config(state="disabled")
        install_button.config(state="disabled")
        uninstall_button.config(state="disabled")
        time.sleep(5)
        clear()

def switch_theme():
    """切换主题"""
    if switch.get():
        sv_ttk.set_theme("dark")
        save_theme("dark")
    else:
        sv_ttk.set_theme("light")
        save_theme("light")

def save_theme(theme):
    """保存主题设置"""
    with open(os.path.join(SAVED_DIR, "theme.txt"), "w") as a:
        a.write(theme)

def load_theme():
    """加载主题设置"""
    try:
        with open(os.path.join(SAVED_DIR, "theme.txt"), "r") as r:
            theme = r.read()
        if theme == "dark":
            switch.set(True)
            sv_ttk.set_theme("dark")
        elif theme == "light":
            switch.set(False)
            sv_ttk.set_theme("light")
    except Exception:
        sv_ttk.set_theme("light")

def update():
    """检查更新"""
    r = requests.get("https://githubtohaoyangli.github.io/info/info.json")
    ver = r.json()["releases"]["release1"]["version"]
    myver = "1.1.0"
    if ver > myver:
        pass

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Python_Tool")
    root.resizable(False, False)
    icon_path = os.path.join(MY_PATH, 'pythontool.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    note = ttk.Notebook(root)
    download_frame = ttk.Frame(note, padding="10")
    pip_frame = ttk.Frame(note, padding="10")
    note.add(download_frame, text="Python Download")
    note.add(pip_frame, text="pip Management")
    note.grid(padx=10, pady=10, row=0, column=0)

    # Python Download Frame
    version_label = ttk.Label(download_frame, text="Select Python Version:")
    version_label.grid(row=0, column=0, pady=5, sticky="e")
    version_combobox = ttk.Combobox(download_frame, values=VERSIONS, state="readonly")
    version_combobox.grid(row=0, column=1, pady=5, padx=5, sticky="w")
    version_combobox.current(0)

    destination_label = ttk.Label(download_frame, text="Select Destination:")
    destination_label.grid(row=1, column=0, pady=5, sticky="e")
    destination_entry = ttk.Entry(download_frame, width=40)
    destination_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")
    select_button = ttk.Button(download_frame, text="Select Path", command=select_destination)
    select_button.grid(row=1, column=2, pady=5, padx=5, sticky="w")

    thread_label = ttk.Label(download_frame, text="Select Number of Threads:")
    thread_label.grid(row=2, column=0, pady=5, sticky="e")
    thread_combobox = ttk.Combobox(download_frame, values=[str(i) for i in range(1, 33)], state="readonly")
    thread_combobox.grid(row=2, column=1, pady=5, padx=5, sticky="w")
    thread_combobox.current(3)  # Default to 4 threads

    download_button = ttk.Button(download_frame, text="Download Selected Version", command=download_selected_version)
    download_button.grid(row=3, column=0, columnspan=3, pady=10, padx=5)
    cancel_button = ttk.Button(download_frame, text="Cancel Download", command=confirm_cancel_download)
    cancel_button.grid(row=4, column=0, pady=10, padx=5,columnspan=3)
    cancel_button.config(state="disabled")

    progress_bar = ttk.Progressbar(download_frame, orient='horizontal', length=300, mode='determinate')
    progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=5)
    status_label = ttk.Label(download_frame, text="", padding="5")
    status_label.grid(row=6, column=0, columnspan=3, pady=5, padx=5)

    # pip Management Frame
    pip_upgrade_button = ttk.Button(pip_frame, text="Upgrade pip", command=upgrade_pip)
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=10, padx=5)
    package_label = ttk.Label(pip_frame, text="Enter Package Name:")
    package_label.grid(row=1, column=0, pady=5, padx=5, sticky="e")
    package_entry = ttk.Entry(pip_frame, width=40)
    package_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")
    install_button = ttk.Button(pip_frame, text="Install Package", command=install_package)
    install_button.grid(row=2, column=0, columnspan=3, pady=10, padx=5)
    uninstall_button = ttk.Button(pip_frame, text="Uninstall Package", command=uninstall_package)
    uninstall_button.grid(row=3, column=0, columnspan=3, pady=10, padx=5)
    package_status_label = ttk.Label(pip_frame, text="", padding="5")
    package_status_label.grid(row=4, column=0, columnspan=3, pady=5, padx=5)

    switch = tk.BooleanVar()
    themes = ttk.Checkbutton(root, text="Dark Mode", variable=switch, style="Switch.TCheckbutton", command=switch_theme)
    themes.grid(row=1, column=0, pady=10, padx=5, sticky="w")
    load_theme()

    check_python_installation()
    root.mainloop()