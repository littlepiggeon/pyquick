import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os
import threading
import requests
import sv_ttk
import wget
import json
from math import sqrt
import time

def clear_status_py():
    status_label_python.config(text="")

    

def clear_status_pip():
    status_label_pip.config(text="")


VERSIONS = [
    "3.12.1",
    "3.12.0",
    "3.11.7",
    "3.11.6",
    "3.11.5",
    "3.11.4",
    "3.11.3",
    "3.11.2",
    "3.11.1",
    "3.11.0",
    "3.10.11",
    "3.10.10",
    "3.10.9",
    "3.10.8",
    "3.10.7",
    "3.10.6",
    "3.10.5",
    "3.10.4",
    "3.10.3",
    "3.10.2",
    "3.10.1",
    "3.10.0",
    "3.9.13",
    "3.9.12",
    "3.9.11",
    "3.9.10",
    "3.9.9",
    "3.9.8",
    "3.9.7",
    "3.9.6",
    "3.9.5",
    "3.9.4",
    "3.9.3",
    "3.9.2",
    "3.9.1",
    "3.9.0",
    "3.8.10",
    "3.8.9",
    "3.8.8",
    "3.8.7",
    "3.8.6",
    "3.8.5",
    "3.8.4",
    "3.8.3",
    "3.8.2",
    "3.8.1",
    "3.8.0",
    "3.7.9",
    "3.7.8",
    "3.7.7",
    "3.7.6",
    "3.7.5",
    "3.7.4",
    "3.7.3",
    "3.7.2",
    "3.7.1",
    "3.7.0",
    "3.6.8",
    "3.6.7",
    "3.6.6",
    "3.6.5",
    "3.6.4",
    "3.6.3",
    "3.6.2",
    "3.6.1",
    "3.6.0",
    "3.5.4",
    "3.5.3",
    "3.5.2",
    "3.5.1",
    "3.5.0",
    "3.4.4",
    "3.4.3",
    "3.4.2",
    "3.4.1",
    "3.4.0",
    "3.3.5",
    "3.3.4",
    "3.3.3",
    "3.3.2",
    "3.3.1",
    "3.3.0",
    "3.2.5",
    "3.2.4",
    "3.2.3",
    "3.2.2",
    "3.2.1",
    "3.2",
    "3.1.4",
    "3.1.3",
    "3.1.2",
    "3.1.1",
    "3.1",
    "3.0.1",
    "3.0",
    "2.7.18",
    "2.7.17",
    "2.7.16",
    "2.7.15",
    "2.7.14",
    "2.7.13",
    "2.7.12",
    "2.7.11",
    "2.7.10",
    "2.7.9",
    "2.7.8",
    "2.7.7",
    "2.7.6",
    "2.7.5",
    "2.7.4",
    "2.7.3",
    "2.7.2",
    "2.7.1",
    "2.7",
    "2.6.6",
    "2.6.5",
    "2.6.4",
    "2.6.3",
    "2.6.2",
    "2.6.1",
    "2.6",
    "2.5.4",
    "2.5.3",
    "2.5.2",
    "2.5.1",
    "2.5",
    "2.4.4",
    "2.4.3",
    "2.4.2",
    "2.4.1",
    "2.4",
    "2.3.5",
    "2.3.4",
    "2.3.3",
    "2.3.2",
    "2.3.1",
    "2.3",
    "2.2.3",
    "2.2.2",
    "2.2.1",
    "2.2",
]




# 保存主题设置到文件
def save_theme_settings(theme):
    with open('theme_settings.json', 'w') as file:
        json.dump({'theme': theme}, file)

#加载theme
def load_theme_settings():
    try:
        with open('theme_settings.json', 'r') as file:
            settings = json.load(file)
            return settings['theme']
    except FileNotFoundError:
        return 'light'

#更改theme
def on_theme_change(event):
    selected_theme = theme_combobox.get()

    if selected_theme == "light":
        sv_ttk.use_light_theme()
    elif selected_theme == "dark":
        sv_ttk.use_dark_theme()

    save_theme_settings(selected_theme)
#应用theme
def update_combobox():
    current_theme = load_theme_settings()
    theme_combobox.set(current_theme)
    on_theme_change(None)  # 应用上次保存的主题


#下载选择版本
def download_selected_version():
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()

    if not os.path.exists(destination_path):
        status_label.config(text="Invalid path!")
        return

    download_thread = threading.Thread(target=download_file, args=(selected_version, destination_path))
    download_thread.setDaemon(True)
    download_thread.start()
def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)


def download_file(selected_version, destination_path):
    sa=selected_version.split(".")
    sb=sa[1]
    sb=int(sb)
    sc=int(sa[0])
    if sc==2 and sb>=5:
        if x86.get():
            file_name = f"python-{selected_version}.msi"
        else:
            file_name = f"python-{selected_version}.amd64.msi"
    elif sc==3 and sb<=4:
        if x86.get():
            file_name = f"python-{selected_version}.msi"
        else:
            file_name = f"python-{selected_version}.amd64.msi"
    elif sc==2 and sb==4:
        file_name = f"python-{selected_version}.msi"
    elif sc==3 and sb>=5:
        if x86.get():
            file_name = f"python-{selected_version}.exe"
        else:
            file_name = f"python-{selected_version}-amd64.exe"
    elif sc==2 and sb<=3:
        file_name = f"Python-{selected_version}.exe"
    destination = os.path.join(destination_path, file_name)

    if os.path.exists(destination):
        os.remove(destination)


    start_time = None
    downloaded_bytes = 0
    update_count = 0  # 设置更新计数器

    def progress_bar_hook(current, total, width=80):
        nonlocal start_time, downloaded_bytes, update_count

        if start_time is None:
            start_time = time.time()

        elapsed_time = time.time() - start_time
        downloaded_bytes = current
        downloaded_mb = downloaded_bytes / (1024 * 1024)
        total_mb = total / (1024 * 1024)

        if elapsed_time > 0:
            download_speed = downloaded_bytes / elapsed_time / (1024 * 1024)  # MB/s
        else:
            download_speed = 0

        progress = int(current / total * 100)

        # 每10次更新MB显示，更新一次进度条
        if update_count % 10 == 0:
            progress_bar['value'] = progress
            status_label.config(text=f"Downloading: {downloaded_mb:.2f} MB / {total_mb:.2f} MB "
                                     f"({download_speed:.2f} MB/s)")
            root.update_idletasks()

        update_count += 1
    def download():
        try:
            sa=selected_version.split(".")
            sb=sa[1]
            sb=int(sb)
            sc=int(sa[0])
            if sc==2 and sb>=5:
                if x86.get():
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.msi"
                else:
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.amd64.msi"
            elif sc==3 and sb<=4:
                if x86.get():
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.msi"
                else:
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.amd64.msi"
            elif sc==2 and sb==4:
                url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.msi"
            elif sc==2 and sb<=3:
                url = f"https://www.python.org/ftp/python/{selected_version}/Python-{selected_version}.exe"
            elif sc==3 and sb>=5:
                if x86.get():
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}.exe"
                else:
                    url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-amd64.exe"
                
            
            wget.download(url, out=destination, bar=progress_bar_hook)
            status_label.config(text="Download Complete!")
            if start_after_download.get():
                os.startfile(destination)
            root.after(5000, clear_status_py)
        except Exception as e:
            status_label.config(text=f"Download Failed: {str(e)}")
            root.after(5000, clear_status_py)

    download_thread = threading.Thread(target=download)
    download_thread.setDaemon(True)
    download_thread.start()


#root.after(5000, clear_status_pip)
def hide_console(command):
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        startupinfo=startup_info
    )

def check_pip_version():
    try:
        pip_version = hide_console(["pip", "--version"]).communicate()[0].decode().split()[1].strip()
        r = requests.get("https://pypi.org/pypi/pip/json")
        latest_version = r.json()["info"]["version"]

        if pip_version != latest_version:
            hide_console(["python", "-m", "pip", "install", "--upgrade", "pip"]).communicate()
            status_label_pip.config(text="pip has been updated!")
            root.after(5000, clear_status_pip)
        else:
            status_label_pip.config(text="pip is up to date")
            root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
    

    


def upgrade_pip():
    try:
        check_pip_version()
    except FileNotFoundError:
        status_label_pip.config(text="Python is not installed.")
        root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)
    
#FileNotFoundError
def check_installed_package(package_name):
    try:
        button_install.config(state="disabled")
        output = subprocess.check_output(["python", "-m", "pip", "show", package_name], text=True,
                                         stderr=subprocess.STDOUT)
        button_install.config(state="enabled")
        return True, f"Package '{package_name}' is already installed."

    except subprocess.CalledProcessError as e:
        button_install.config(state="enabled")
        return False, e.output.strip()


def install_package():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()

        installed, message = check_installed_package(package_name)
        if installed:
            status_label_pip.config(text=message)
        else:
            try:
                button_install.config(state="disabled")
                result = subprocess.run(["python", "-m", "pip", "install", package_name], capture_output=True,
                                        text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout

                if "Successfully installed" in output:
                    status_label_pip.config(text=f"Package '{package_name}' has been installed successfully!")
                    button_install.config(state="enabled")
                    root.after(5000, clear_status_pip)
                else:
                    status_label_pip.config(text=f"Error installing package '{package_name}': {output}")
                    button_install.config(state="enabled")
                    root.after(5000, clear_status_pip)
            except Exception as e:
                status_label_pip.config(text=f"Error installing package '{package_name}': {str(e)}")
                button_install.config(state="enabled")
                root.after(5000, clear_status_pip)

                pack_thread = threading.Thread(target=install_package)
                pack_thread.setDaemon(True)
                pack_thread.start()
    except FileNotFoundError:
        status_label_pip.config(text="Python is not installed.")
        root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)

def uninstall_package():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()

        try:
            installed_packages = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True,
                                                         creationflags=subprocess.CREATE_NO_WINDOW)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python", "-m", "pip", "uninstall", "-y", package_name], capture_output=True,
                                        text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout

                if "Successfully uninstalled" in output:
                    status_label_pip.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                    root.after(5000, clear_status_pip)
                else:
                    status_label_pip.config(text=f"Error uninstalling package '{package_name}': {output}")
            else:
                status_label_pip.config(text=f"Package '{package_name}' is not installed.")
                root.after(5000, clear_status_pip)
        except Exception as e:
            status_label_pip.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
            root.after(5000, clear_status_pip)
    except FileNotFoundError:
        status_label_pip.config(text="Python is not installed.")
        root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)
    uninstall_thread = threading.Thread(target=uninstall_package)
    uninstall_thread.setDaemon(True)
    uninstall_thread.start()
def backup_pip_packages():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            result = subprocess.run(["pip", "freeze"], text=True, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE)
            output = result.stdout
            with open("requirements.txt", "w") as file:
                file.write(output)
            status_label_pip.config(text="Pip packages backed up to 'requirements.txt'")
            root.after(5000, clear_status_pip)
        except Exception as e:
            status_label_pip.config(text=f"Error backing up pip packages: {str(e)}")
            root.after(5000, clear_status_pip)
    except FileNotFoundError:
        status_label_pip.config(text="python is not installed.")
        root.after(5000, clear_status_pip)
def check_python_installation():
    try:
        subprocess.check_output(["python", "--version"])
    except Exception as e:
        status_label_pip.config(text="Python is not installed.")
        root.after(5000, clear_status_pip)
        return False
    return True

def is_package_installed(package):
    result = subprocess.run(["pip", "show", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW, text=True)
    return result.returncode == 0

def uninstall_from_requirements():
    try:
        if not check_python_installation():
            return

        if not os.path.exists("requirements.txt"):
            status_label_pip.config(text="requirements.txt not found")
            root.after(5000, clear_status_pip)
            return

        with open("requirements.txt", "r") as file:
            packages = file.readlines()

        all_packages_uninstalled = True
        for package in packages:
            package = package.strip()
            result = subprocess.run(["pip", "uninstall", "-y", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    creationflags=subprocess.CREATE_NO_WINDOW, text=True)
            if result.returncode != 0:
                all_packages_uninstalled = False

        if all_packages_uninstalled:
            status_label_pip.config(text="All packages are uninstalled")
        else:
            status_label_pip.config(text="Some packages are not installed")

        root.after(5000, clear_status_pip)

    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)

def install_from_requirements():
    try:
        if not check_python_installation():
            return

        if not os.path.exists("requirements.txt"):
            status_label_pip.config(text="requirements.txt not found")
            root.after(5000, clear_status_pip)
            return

        with open("requirements.txt", "r") as file:
            packages = file.readlines()

        failed_packages = []

        for package in packages:
            package = package.strip()
            if not is_package_installed(package):
                result = subprocess.run(["pip", "install", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW, text=True)
                if result.returncode != 0:
                    failed_packages.append(package)

        if not failed_packages:
            status_label_pip.config(text="All packages installed successfully!")
        else:
            status_label_pip.config(text=f"Some packages failed to install: {', '.join(failed_packages)}")

        root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)

def uninstall_from_requirements():
    
    try:
        # 读取 requirements.txt 文件
        if not os.path.exists("requirements.txt"):
            status_label_pip.config(text="requirements.txt not found")
            root.after(5000, clear_status_pip)
            return

        with open("requirements.txt", "r") as file:
            packages = file.readlines()

        # 卸载每个包
        all_packages_uninstalled = True
        for package in packages:
            package = package.strip()
            result = subprocess.run(["pip", "uninstall", "-y", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    creationflags=subprocess.CREATE_NO_WINDOW, text=True)

            if result.returncode != 0:
                all_packages_uninstalled = False

        # 显示相应的消息
        if all_packages_uninstalled:
            status_label_pip.config(text="All packages are uninstalled")
        else:
            status_label_pip.config(text="Some packages are not installed")

        root.after(5000, clear_status_pip)

    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)
    backup_thread = threading.Thread(target=uninstall_from_requirements)
    backup_thread.start()

def is_package_installed(package):
    
    # 检查包是否已安装
    result = subprocess.run(["pip", "show", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW, text=True)
    return result.returncode == 0

def install_from_requirements():
    backup_thread = threading.Thread(target=install_from_requirements)
    backup_thread.start()
    try:
        if not os.path.exists("requirements.txt"):
            status_label_pip.config(text="requirements.txt not found")
            root.after(5000, clear_status_pip)
            return

        with open("requirements.txt", "r") as file:
            packages = file.readlines()

        failed_packages = []

        for package in packages:
            package = package.strip()
            if not is_package_installed(package):
                result = subprocess.run(["pip", "install", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW, text=True)
                if result.returncode != 0:
                        adp=failed_packages.append
                        adp(sqrt(package))

        if not failed_packages:
                status_label_pip.config(text="All packages installed successfully!")
        else:
                status_label_pip.config(text=f"Some packages failed to install: {', '.join(failed_packages)}")

        root.after(5000, clear_status_pip)
    except Exception as e:
        status_label_pip.config(text=f"Error: {str(e)}")
        root.after(5000, clear_status_pip)

def check_python_installation_a():
    try:
        subprocess.check_output(["python", "--version"])
    except FileNotFoundError:
        status_label_pip.config(text="Python is not installed.")
        status_label_python.config(text="Python is not installed.")
        button_pip_upgrade.config(state="disabled")
        package_entry.config(state="disabled")
        button_install.config(state="disabled")
        button_uninstall.config(state="disabled")
        backup_button.config(state="disabled")
        uninstall_button.config(state="disabled")
        install_button.config(state="disabled")



root = tk.Tk()
root.title("Python tool")

tab_control = ttk.Notebook(root)

tab_python = ttk.Frame(tab_control)
tab_control.add(tab_python, text='Python Downloader')
tab_control.pack(expand=1, fill='both', padx=10, pady=10)

# Python Downloader Tab
frame_python_downloader = ttk.Frame(tab_python)
frame_python_downloader.pack(padx=20, pady=20)

version_combobox = ttk.Combobox(frame_python_downloader, values=VERSIONS, state="readonly", width=20)
version_combobox.pack(pady=5)

destination_entry = ttk.Entry(frame_python_downloader, width=40)
destination_entry.pack(pady=5)
 
button_select = ttk.Button(frame_python_downloader, text="Select Path", command=select_destination)
button_select.pack(pady=5)

button_download = ttk.Button(frame_python_downloader, text="Download", command=download_selected_version)
button_download.pack(pady=5)

x86 = tk.BooleanVar()  # 创建一个BooleanVar变量，用于检测复选框状态
xx = ttk.Checkbutton(frame_python_downloader, text="download x86(not amd64,>=python 2.5)", variable=x86, style="Switch.TCheckbutton",command=x86)
xx.pack()


start_after_download = tk.BooleanVar()  # 创建一个BooleanVar变量，用于检测复选框状态
checkbutton = ttk.Checkbutton(frame_python_downloader, text="Start after download", variable=start_after_download, style="Switch.TCheckbutton",command=start_after_download)
checkbutton.pack()



progress_bar = ttk.Progressbar(frame_python_downloader, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)
status_label = ttk.Label(frame_python_downloader, text="")
status_label.pack()


# 新增：在下载完成后调用启动函数


status_label_python = ttk.Label(frame_python_downloader, text="")
status_label_python.pack()

# Pip Tab
tab_pip = ttk.Frame(tab_control)
tab_control.add(tab_pip, text='Pip')
tab_control.pack(expand=1, fill='both', padx=10, pady=10)

frame_pip = ttk.Frame(tab_pip)
frame_pip.pack(padx=20, pady=20)

button_pip_upgrade = ttk.Button(frame_pip, text="Upgrade pip", command=upgrade_pip, width=20)
button_pip_upgrade.pack(pady=5)

package_entry = ttk.Entry(frame_pip, width=30)
package_entry.pack(pady=5)

button_install = ttk.Button(frame_pip, text="Install Package", command=install_package, width=20)
button_install.pack(pady=5)

button_uninstall = ttk.Button(frame_pip, text="Uninstall Package", command=uninstall_package, width=20)
button_uninstall.pack(pady=5)

backup_button = ttk.Button(frame_pip, text="Backup Pip Packages", command=backup_pip_packages)
backup_button.pack(pady=5)

uninstall_button = ttk.Button(frame_pip, text="Uninstall from requirements.txt", command=uninstall_from_requirements)
uninstall_button.pack(pady=5)
install_button = ttk.Button(frame_pip, text="Install from requirements.txt", command=install_from_requirements)
install_button.pack()
status_label_pip = ttk.Label(frame_pip, text="")
status_label_pip.pack()

# 新增：Settings Tab
tab_theme = ttk.Frame(tab_control)
tab_control.add(tab_theme, text='toggle theme')
tab_control.pack(expand=1, fill='both', padx=10, pady=10)

frame_theme = ttk.Frame(tab_theme)
frame_theme.pack(padx=20, pady=20)

label_toggle_theme = ttk.Label(frame_theme, text="Toggle Theme")
label_toggle_theme.pack(side=tk.LEFT, padx=5)

theme_combobox = ttk.Combobox(frame_theme, values=["light", "dark"], state="readonly")
theme_combobox.pack(side=tk.LEFT, pady=5)
theme_combobox.bind("<<ComboboxSelected>>", on_theme_change)

status_label_settings = ttk.Label(frame_theme, text="")
status_label_settings.pack()

update_combobox()  # 更新初始状态为当前主题
load_theme_settings()
check_python_installation_a()
root.iconbitmap('python.ico')
root.mainloop()
