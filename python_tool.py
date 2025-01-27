import datetime
import logging
import os
import re
import subprocess
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, filedialog, messagebox

import requests
import sv_ttk
import urllib3
from bs4 import BeautifulSoup

# 禁用 SSL 警告
urllib3.disable_warnings()

# 获取当前工作目录
MY_PATH = os.getcwd()

# 获取用户配置目录
config_path = os.path.join(os.environ["APPDATA"], f"pyquick")

# 如果保存目录不存在，则创建它
if not os.path.exists(config_path):
    os.makedirs(config_path)


def show_about():
    """显示关于对话框"""
    if datetime.datetime.now() >= datetime.datetime(2025, 2, 1):
        time_lim = (datetime.datetime(2025, 4, 13) - datetime.datetime.now()).days
        messagebox.showwarning("About",
                               f"Version: 2.0 dev\nBuild: 1911\nExpiration time:2025/3/13\n only {time_lim} days left.")
    else:
        time_lim = (datetime.datetime(2025, 4, 13) - datetime.datetime.now()).days
        messagebox.showinfo("About", f"Version: 2.0 dev\nBuild: 1911\nExpiration time:2025/3/13\n{time_lim} days left.")


# 全局变量
file_size = 0
executor: ThreadPoolExecutor
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


class Version:
    def __init__(self, version_str: str):
        self.version = version_str.split('.')
        while len(self.version) < 3:
            self.version.append('0')

    def __lt__(self, other):
        for i in range(3):
            if (v1 := int(self.version[i])) < (v2 := int(other.version[i])):
                return True
            elif v1 > v2:
                return False
        else:
            return False


# 排序版本获取结果
def sort_results(results: list):
    _results = results.copy()
    length = len(_results)
    for i in range(length):
        for ii in range(0, length - i - 1):
            v1 = Version(_results[ii])
            v2 = Version(_results[ii + 1])
            if v1 < v2:
                _results[ii], _results[ii + 1] = _results[ii + 1], _results[ii]
    version_combobox.configure(values=_results)


# 获取可下载版本列表
def python_version_reload():
    version_reload_button.configure(state="disabled", text="Reloading...")
    root.update()
    try:
        with requests.get("https://www.python.org/ftp/python/") as r:
            bs = BeautifulSoup(r.content, "lxml")
            results = []
            for i in bs.find_all("a"):
                if i.text[0].isnumeric():
                    results.append(i.text[:-1])
            if results:
                version_reload_button.configure(text="Sorting...")
                sort_results(results)
    except Exception as e:
        logging.error(f"Python Version Reload Wrong:{e}")
    version_reload_button.configure(state="normal", text="Reload")
    root.update()


def validate_version(version):
    """
    验证版本号格式是否符合预期的格式

    此函数通过正则表达式检查传入的版本号是否符合 major.minor.patch 的格式，
    其中 major、minor 和 patch 都是数字

    参数:
    version (str): 需要验证的版本号字符串

    返回:
    bool: 如果版本号符合预期格式，则返回 True，否则返回 False
    """
    # 定义版本号的正则表达式模式，确保版本号是 major.minor.patch 的格式
    pattern = r'^\d+\.\d+\.\d+$'
    # 使用正则表达式匹配版本号，返回匹配结果的布尔值
    return bool(re.match(pattern, version))


def validate_path(path):
    """
    验证路径是否存在

    参数:
    path (str): 需要验证的路径

    返回:
    bool: 如果路径存在返回True，否则返回False
    """
    return os.path.isdir(path)


def download_chunk(url, start_byte, end_byte, destination, retries=3):
    """
    下载文件的指定部分

    :param url: 文件的URL
    :param start_byte: 开始下载的字节位置
    :param end_byte: 结束下载的字节位置
    :param destination: 文件保存的目标路径
    :param retries: 最大重试次数，默认为3次
    :return: 如果下载成功返回True，否则返回False
    """
    global is_downloading
    # 构造请求头，指定下载的字节范围
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    attempt = 0
    # 尝试下载文件，如果失败则重试
    while attempt < retries:
        try:
            # 发起HTTP请求，包含自定义请求头，启用流式响应，设置超时
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            # 检查响应状态码，如果状态码表示错误，则抛出异常
            response.raise_for_status()
            # 使用文件锁确保并发安全，打开文件准备写入
            with lock:
                with open(destination, 'r+b') as f:
                    f.seek(start_byte)
                    # 遍历响应内容，写入到文件中
                    for chunk in response.iter_content(chunk_size=8192):
                        if not is_downloading:
                            return False
                        f.write(chunk)
                        downloaded_bytes[0] += len(chunk)
            return True
        except requests.RequestException as e:
            # 如果发生网络请求异常，更新状态标签并重试
            with lock:
                status_label.config(text=f"Download Failed! Retrying... ({attempt + 1}/{retries})")
            attempt += 1
    # 如果重试次数用尽仍然失败，更新状态标签并设置下载状态为False
    with lock:
        status_label.config(text=f"Download Failed! Error: {e}")
        is_downloading = False
    return False


# 定义下载指定版本Python安装程序的函数
def download_file(selected_version, destination_path, num_threads):
    """下载指定版本的Python安装程序"""
    global file_size, executor, futures, downloaded_bytes, is_downloading, destination
    # 验证版本号是否有效
    if not validate_version(selected_version):
        status_label.config(text="Invalid version number")
        root.after(5000, clear)
        return

    # 验证目标路径是否有效
    if not validate_path(destination_path):
        status_label.config(text="Invalid destination path")
        root.after(5000, clear)
        return

    # 构造文件名和目标路径
    file_name = f"python-{selected_version}-amd64.exe"
    destination = os.path.join(destination_path, file_name)

    # 如果目标文件已存在，尝试删除它
    if os.path.exists(destination):
        try:
            os.remove(destination)
        except (PermissionError, FileNotFoundError) as e:
            status_label.config(text=f"Failed to remove existing file: {str(e)}")
            root.after(5000, clear)
            return

    # 构造下载URL
    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-amd64.exe"

    # 获取文件大小
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        file_size = int(response.headers['Content-Length'])
    except requests.RequestException as e:
        status_label.config(text=f"Failed to get file size: {str(e)}")
        root.after(5000, clear)
        return

    # 尝试创建目标文件
    try:
        with open(destination, 'wb') as f:
            pass
    except IOError as e:
        status_label.config(text=f"Failed to create file: {str(e)}")
        root.after(5000, clear)
        return

    # 计算每个线程下载的数据块大小
    chunk_size = file_size // num_threads
    futures = []
    downloaded_bytes = [0]
    is_downloading = True

    # 使用线程池执行下载任务
    executor = ThreadPoolExecutor(max_workers=num_threads)
    for i in range(num_threads):
        start_byte = i * chunk_size
        end_byte = start_byte + chunk_size - 1 if i != num_threads - 1 else file_size - 1

        def start():
            futures.append(executor.submit(download_chunk, url, start_byte, end_byte, destination))

        threading.Thread(target=start, daemon=True).start()

    # 启动一个线程来更新下载进度
    threading.Thread(target=update_progress, daemon=True).start()
    # 启用取消下载按钮
    cancel_button.config(state="normal")


def update_progress():
    """更新进度条和状态标签

    通过计算已下载字节数与总文件大小的比例来更新进度条和状态标签的文本。
    此函数在一个单独的线程中运行，以保持UI响应性。
    """
    global file_size, is_downloading
    # 当有任何一个下载任务未完成时，继续更新进度
    while any(not future.done() for future in futures):
        # 如果下载状态为False，则停止更新进度
        if not is_downloading:
            break
        # 计算并更新下载进度的百分比
        progress = int(downloaded_bytes[0] / file_size * 100)
        # 将已下载字节数转换为MB
        downloaded_mb = downloaded_bytes[0] / (1024 * 1024)
        # 将总文件大小转换为MB
        total_mb = file_size / (1024 * 1024)
        # 更新状态标签的文本，显示下载进度和已下载/总文件大小
        status_label.config(text=f"Progress: {progress}% ({downloaded_mb:.2f} MB / {total_mb:.2f} MB)")
        # 更新进度条的值
        progress_bar['value'] = progress
        # 暂停0.1秒，减少UI更新频率
        time.sleep(0.05)
    # 如果下载状态为True，则表示下载已完成
    if is_downloading:
        status_label.config(text="Download Complete!")
    # 如果下载状态为False，则表示下载已取消
    else:
        status_label.config(text="Download Cancelled!")
    # 将下载状态设置为False，表示下载已完成或已取消
    is_downloading = False
    # 禁用取消下载按钮，防止用户在下载已完成或已取消的情况下点击按钮
    cancel_button.config(state="disabled")


def cancel_download():
    """取消正在进行的下载"""
    global is_downloading
    is_downloading = False
    if executor:
        executor.shutdown(wait=False)
        cancel_button.config(state="disabled")  # 禁用取消下载按钮
        progress_bar['value'] = 0
        time.sleep(0.5)
        os.remove(destination)


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
        threading.Thread(target=cancel_download, daemon=True).start()


def get_pip_version():
    """获取当前pip版本"""
    try:
        return subprocess.check_output(["pip", "--version"],
                                       creationflags=subprocess.CREATE_NO_WINDOW).decode().strip().split()[1]
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
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"],
                       creationflags=subprocess.CREATE_NO_WINDOW)
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
                result = subprocess.run(["python", "-m", "pip", "install", package_name], capture_output=True,
                                        text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                installed = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True,
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
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
            installed_packages = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True,
                                                         creationflags=subprocess.CREATE_NO_WINDOW)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python", "-m", "pip", "uninstall", "-y", package_name], capture_output=True,
                                        text=True, creationflags=subprocess.CREATE_NO_WINDOW)
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
    except:
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
    with open(os.path.join(config_path, "theme.txt"), "w") as a:
        a.write(theme)


def load_theme():
    """加载主题设置"""
    try:
        with open(os.path.join(config_path, "theme.txt"), "r") as r:
            theme = r.read()
        if theme == "dark":
            switch.set(True)
            sv_ttk.set_theme("dark")
        elif theme == "light":
            switch.set(False)
            sv_ttk.set_theme("light")
    except:
        sv_ttk.set_theme("light")


def update():
    """检查更新"""
    r = requests.get("https://githubtohaoyangli.github.io/info/info.json")
    ver = r.json()["releases"]["release1"]["version"]
    myver = "1.1.0"
    if ver > myver:
        pass


if __name__ == "__main__":
    if datetime.datetime.now() >= datetime.datetime(2025, 3, 13):
        messagebox.showerror("Error", "This program cannot be opened after March 13, 2025.")
        exit(1)
    root = tk.Tk()
    root.title("Python_Tool")
    root.resizable(False, False)
    icon_path = os.path.join(MY_PATH, 'pyquick.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # 添加 Help 菜单项
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)

    note = ttk.Notebook(root)
    download_frame = ttk.Frame(note, padding="10")
    pip_frame = ttk.Frame(note, padding="10")
    note.add(download_frame, text="Python Download")
    note.add(pip_frame, text="pip Management")
    note.grid(padx=10, pady=10, row=0, column=0)

    # Python Download Frame
    version_label = ttk.Label(download_frame, text="Select Python Version:")
    version_label.grid(row=0, column=0, pady=5, sticky="e")
    version_combobox = ttk.Combobox(download_frame, values=[''], state="readonly")
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
    thread_combobox = ttk.Combobox(download_frame, values=[str(i) for i in range(1, 1025)], state="readonly")
    thread_combobox.grid(row=2, column=1, pady=5, padx=5, sticky="w")
    thread_combobox.current(31)  # Default to 32 threads

    download_button = ttk.Button(download_frame, text="Download Selected Version", command=download_selected_version)
    download_button.grid(row=3, column=0, columnspan=3, pady=10, padx=5)
    cancel_button = ttk.Button(download_frame, text="Cancel Download", command=confirm_cancel_download)
    cancel_button.grid(row=4, column=0, pady=10, padx=5, columnspan=3)
    cancel_button.config(state="disabled")

    version_reload_button = ttk.Button(download_frame, text="Reload", command=python_version_reload)
    version_reload_button.grid(row=0, column=2, sticky="w")

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
