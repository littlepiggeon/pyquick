import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os
import threading
import requests
import sv_ttk
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings()

# 获取当前工作目录
my_path = os.getcwd()

# 如果保存目录不存在，则创建它
if not os.path.exists(f"{my_path}\\saved"):
    os.mkdir(f"{my_path}\\saved")

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

def clear():
    status_label.config(text="")
    package_label.config(text="Enter Package Name:")

def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)

def validate_version(version):
    import re
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))

def validate_path(path):
    return os.path.isdir(path)

def download_chunk(url, start_byte, end_byte, destination, lock, downloaded_bytes, queue):
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        with lock:
            with open(destination, 'r+b') as f:
                f.seek(start_byte)
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_bytes[0] += len(chunk)
                    queue.put((downloaded_bytes[0], file_size))  # 发送进度信息到队列
    except requests.RequestException as e:
        with lock:
            queue.put(('error', str(e)))  # 发送错误信息到队列

def update_progress(downloaded_bytes, file_size):
    progress = int(downloaded_bytes / file_size * 100)
    downloaded_mb = downloaded_bytes / (1024 * 1024)
    total_mb = file_size / (1024 * 1024)
    status_label.config(text=f"Progress: {progress}% ({downloaded_mb:.2f} MB / {total_mb:.2f} MB)")
    progress_bar['value'] = progress

def process_queue(queue):
    try:
        while True:
            item = queue.get_nowait()
            if isinstance(item, tuple):
                downloaded_bytes, file_size = item
                update_progress(downloaded_bytes, file_size)
            elif isinstance(item, str) and item == 'error':
                status_label.config(text="Download Failed!")
                break
            elif isinstance(item, str) and item == 'complete':
                status_label.config(text="Download Complete!")
                break
            queue.task_done()
    except queue.Empty:
        pass
    root.after(100, process_queue, queue)  # 每 100 毫秒检查一次队列

def download_file(selected_version, destination_path, num_threads):
    global file_size
    if not validate_version(selected_version):
        root.after(0, lambda: status_label.config(text="Invalid version number"))
        root.after(5000, clear)
        return

    if not validate_path(destination_path):
        root.after(0, lambda: status_label.config(text="Invalid destination path"))
        root.after(5000, clear)
        return

    file_name = f"python-{selected_version}-amd64.exe"
    destination = os.path.join(destination_path, file_name)

    if os.path.exists(destination):
        try:
            os.remove(destination)
        except (PermissionError, FileNotFoundError) as e:
            root.after(0, lambda: status_label.config(text=f"Failed to remove existing file: {str(e)}"))
            root.after(5000, clear)
            return

    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-amd64.exe"

    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        file_size = int(response.headers['Content-Length'])
    except requests.RequestException as e:
        root.after(0, lambda: status_label.config(text=f"Failed to get file size: {str(e)}"))
        root.after(5000, clear)
        return

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        root.after(0, lambda: status_label.config(text=f"Network error: {str(e)}"))
        root.after(5000, clear)
        return

    try:
        with open(destination, 'wb') as f:
            pass
    except IOError as e:
        root.after(0, lambda: status_label.config(text=f"Failed to create file: {str(e)}"))
        root.after(5000, clear)
        return

    chunk_size = file_size // num_threads
    futures = []
    lock = threading.Lock()
    downloaded_bytes = [0]
    queue = queue.Queue()  # 显式地定义 queue

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            start_byte = i * chunk_size
            end_byte = start_byte + chunk_size - 1 if i != num_threads - 1 else file_size - 1
            futures.append(executor.submit(download_chunk, url, start_byte, end_byte, destination, lock, downloaded_bytes, queue))

        root.after(100, process_queue, queue)  # 启动队列处理循环


def download_selected_version():
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    num_threads = int(thread_combobox.get())

    if not os.path.exists(destination_path):
        root.after(0, lambda: status_label.config(text="Invalid path!"))
        root.after(5000, clear)
        return

    download_thread = threading.Thread(target=download_file, args=(selected_version, destination_path, num_threads), daemon=True)
    download_thread.start()

def get_pip_version():
    try:
        return subprocess.check_output(["pip", "--version"], creationflags=subprocess.CREATE_NO_WINDOW).decode().strip().split()[1]
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        return None

def get_latest_pip_version():
    try:
        r = requests.get("https://pypi.org/pypi/pip/json", verify=False)
        return r.json()["info"]["version"]
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def update_pip():
    try:
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        return False

def check_pip_version():
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
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        upthread = threading.Thread(target=check_pip_version, daemon=True)
        upthread.start()
    except FileNotFoundError:
        package_label.config(text="Python is not installed.")
        time.sleep(5)
        clear()
    except Exception as e:
        package_label.config(text=f"Error: {str(e)}")
        time.sleep(5)
        clear()

def install_package():
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

        install_thread = threading.Thread(target=install_package_thread)
        install_thread.start()
    except FileNotFoundError:
        package_label.config(text="Python is not installed.")
        time.sleep(5)
        clear()
    except Exception as e:
        package_label.config(text=f"Error: {str(e)}")
        time.sleep(5)
        clear()

def uninstall_package():
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
    if switch.get():
        sv_ttk.set_theme("dark")
        save_theme("dark")
    else:
        sv_ttk.set_theme("light")
        save_theme("light")

def save_theme(theme):
    with open(f"{my_path}\\saved\\theme.txt", "w") as a:
        a.write(theme)

def load_theme():
    try:
        with open(f"{my_path}\\saved\\theme.txt", "r") as r:
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
    r = requests.get("https://githubtohaoyangli.github.io/info/info.json")
    ver = r.json()["releases"]["release1"]["version"]
    myver = "1.1.0"
    if ver > myver:
        pass

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Python_Tool")
    root.resizable(False, False)
    icon_path = os.path.join(my_path, 'pythontool.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    note = ttk.Notebook(root)
    frame = ttk.Frame(root, padding="10")
    framea = ttk.Frame(root, padding="10")
    note.add(frame, text="Python Download")
    note.add(framea, text="pip Management")
    note.grid(padx=10, pady=10, row=0, column=0)

    version_label = ttk.Label(frame, text="Select Python Version:")
    version_label.grid(row=0, column=0, pady=10, sticky="e")
    selected_version = tk.StringVar()
    version_combobox = ttk.Combobox(frame, textvariable=selected_version, values=VERSIONS, state="readonly")
    version_combobox.grid(row=0, column=1, pady=10, padx=10, sticky="w")
    version_combobox.current(0)

    destination_label = ttk.Label(frame, text="Select Destination:")
    destination_label.grid(row=1, column=0, pady=10, sticky="e")
    destination_entry = ttk.Entry(frame, width=40)
    destination_entry.grid(row=1, column=1, pady=10, padx=10, sticky="w")
    select_button = ttk.Button(frame, text="Select Path", command=select_destination)
    select_button.grid(row=1, column=2, pady=10, padx=10, sticky="w")

    thread_label = ttk.Label(frame, text="Select Number of Threads:")
    thread_label.grid(row=2, column=0, pady=10, sticky="e")
    thread_combobox = ttk.Combobox(frame, values=[str(i) for i in range(1, 9)], state="readonly")
    thread_combobox.grid(row=2, column=1, pady=10, padx=10, sticky="w")
    thread_combobox.current(3)  # Default to 4 threads

    download_button = ttk.Button(frame, text="Download Selected Version", command=download_selected_version)
    download_button.grid(row=3, column=0, columnspan=3, pady=10, padx=10)
    progress_bar = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate')
    progress_bar.grid(row=4, column=0, columnspan=3, pady=10, padx=10)
    status_label = ttk.Label(frame, text="", padding="10")
    status_label.grid(row=5, column=0, columnspan=3, pady=10, padx=10)

    pip_upgrade_button = ttk.Button(framea, text="Upgrade pip", command=upgrade_pip)
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=10, padx=10)
    package_label = ttk.Label(framea, text="Enter Package Name:")
    package_label.grid(row=1, column=0, pady=10, padx=10, sticky="e")
    package_entry = ttk.Entry(framea, width=40)
    package_entry.grid(row=1, column=1, pady=10, padx=10, sticky="w")
    install_button = ttk.Button(framea, text="Install Package", command=install_package)
    install_button.grid(row=2, column=0, columnspan=3, pady=10, padx=10)
    uninstall_button = ttk.Button(framea, text="Uninstall Package", command=uninstall_package)
    uninstall_button.grid(row=3, column=0, columnspan=3, pady=10, padx=10)
    package_status_label = ttk.Label(framea, text="", padding="10")
    package_status_label.grid(row=4, column=0, columnspan=3, pady=10, padx=10)

    switch = tk.BooleanVar()
    themes = ttk.Checkbutton(root, text="Dark Mode", variable=switch, style="Switch.TCheckbutton", command=switch_theme)
    themes.grid(row=1, column=0, pady=10, padx=10, sticky="w")
    load_theme()

    check_python_installation()
    root.mainloop()
