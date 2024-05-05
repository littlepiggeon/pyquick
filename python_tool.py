import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os
import threading
import requests
import sv_ttk
import time
import wget
VERSIONS = [
    "3.12.0",
    "3.11.0",
    "3.10.0",
    "3.9.0",
    "3.8.0",
    "3.7.0",
    "3.6.0",
    "3.5.0"
]
def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)

def download_file(selected_version, destination_path):
    file_name = f"python-{selected_version}-amd64.exe"
    destination = os.path.join(destination_path, file_name)
    
    if os.path.exists(destination):
        os.remove(destination)
    
    def progress_bar_hook(current, total, width=80):
        progress = int(current / total * 100)
        progress_bar['value'] = progress
        downloaded_mb = current / (1024 * 1024)
        status_label.config(text=f"Downloading: {downloaded_mb:.2f} MB / {total / (1024 * 1024):.2f} MB")
        root.update_idletasks()

    try:
        url = f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-amd64.exe"
        # 使用wget下载文件
        wget.download(url, out=destination, bar=progress_bar_hook)
        status_label.config(text="Download Complete!")
    except Exception as e:
        status_label.config(text=f"Download Failed: {str(e)}")

def check_pip_version():
    try:
        pip_version = subprocess.check_output(["pip", "--version"], creationflags=subprocess.CREATE_NO_WINDOW).decode().strip().split()[1]
        r = requests.get("https://pypi.org/pypi/pip/json")
        latest_version = r.json()["info"]["version"]

        if pip_version != latest_version:
            status_label.config(text=f"Current pip version: {pip_version}\nLatest pip version: {latest_version}\nUpdating pip...")
            subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], creationflags=subprocess.CREATE_NO_WINDOW)
            status_label.config(text="pip has been updated!")
        else:
            status_label.config(text=f"pip is up to date: {pip_version}")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

def download_selected_version():
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    
    if not os.path.exists(destination_path):
        status_label.config(text="Invalid path!")
        return
    
    download_thread = threading.Thread(target=download_file, args=(selected_version, destination_path))
    download_thread.start()

def upgrade_pip():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        check_pip_version()
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

def install_package():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()
        
        def install_package_thread():
            try:
                result = subprocess.run(["python", "-m", "pip", "install", package_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if "Successfully installed" in result.stdout:
                    status_label.config(text=f"Package '{package_name}' has been installed successfully!")
                else:
                    status_label.config(text=f"Error installing package '{package_name}': {result.stderr}")
            except Exception as e:
                status_label.config(text=f"Error installing package '{package_name}': {str(e)}")
        
        install_thread = threading.Thread(target=install_package_thread)
        install_thread.start()
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

def uninstall_package():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        package_name = package_entry.get()
        
        try:
            installed_packages = subprocess.check_output(["python", "-m", "pip", "list", "--format=columns"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python", "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if "Successfully uninstalled" in result.stdout:
                    status_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                else:
                    status_label.config(text=f"Error uninstalling package '{package_name}': {result.stderr}")
            else:
                status_label.config(text=f"Package '{package_name}' is not installed.")
        except Exception as e:
            status_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

def check_python_installation():
    try:
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        status_label.config(text="Python is not installed.")
        pip_upgrade_button.config(state="disabled")
        install_button.config(state="disabled")
        uninstall_button.config(state="disabled")
root = tk.Tk()
root.title("Python Downloader")




root.iconbitmap('python.ico')
frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0)

version_label = ttk.Label(frame, text="Select Python Version:")
version_label.grid(row=0, column=0, pady=10)

selected_version = tk.StringVar()
version_combobox = ttk.Combobox(frame, textvariable=selected_version, values=VERSIONS, state="readonly")
version_combobox.grid(row=0, column=1, pady=10)
version_combobox.current(0)

destination_label = ttk.Label(frame, text="Select Destination:")
destination_label.grid(row=1, column=0, pady=10)

destination_entry = ttk.Entry(frame, width=40)
destination_entry.grid(row=1, column=1, pady=10)

select_button = ttk.Button(frame, text="Select Path", command=select_destination)
select_button.grid(row=1, column=2, pady=10)

download_button = ttk.Button(frame, text="Download Selected Version", command=download_selected_version)
download_button.grid(row=2, column=0, columnspan=3, pady=10)

pip_upgrade_button = ttk.Button(frame, text="Upgrade pip", command=upgrade_pip)
pip_upgrade_button.grid(row=3, column=0, columnspan=3, pady=10)
upgrade_pip_button = pip_upgrade_button  # Alias for disabling/enabling later

package_label = ttk.Label(frame, text="Enter Package Name:")
package_label.grid(row=4, column=0, pady=10)

package_entry = ttk.Entry(frame, width=40)
package_entry.grid(row=4, column=1, pady=10)

install_button = ttk.Button(frame, text="Install Package", command=install_package)
install_button.grid(row=5, column=0, columnspan=3, pady=10)

uninstall_button = ttk.Button(frame, text="Uninstall Package", command=uninstall_package)
uninstall_button.grid(row=6, column=0, columnspan=3, pady=10)

progress_bar = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate')
progress_bar.grid(row=7, column=0, columnspan=3, pady=10)

status_label = ttk.Label(frame, text="", padding="10")
status_label.grid(row=8, column=0, columnspan=3)

# Set sv_ttk theme
sv_ttk.set_theme("dark")

check_python_installation()

root.mainloop()
