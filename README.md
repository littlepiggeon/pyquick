# python tool
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/wg.png?raw=true)  
一个用 python `` tkinter, sv_ttk``的小部件（[sv_ttk地址](https://github.com/rdbende/Sun-Valley-ttk-theme)),代码只有200行左右，编译只有30MB左右，可以更好进行python使用  
注意：不能在[liexe(skip)](https://github.com/githubtohaoyangli/liexe-skip-download)使用,因为作为独立程序而不是liexe扩展
# 下载python
支持下载  
```commandline
python 3.12--3.5
```
有下拉菜单选择python版本，并且有漂亮的进度条（中国下载慢一些）  
（debug 1.0有3.13.0选项，但会报错）
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/download.png?raw=true) 
# 升级pip
先检测本地与网上pip版本，才会运行该命令
```commandline
python -m pip install --upguade pip
```
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/pip.png?raw=true)  
# 下载/卸载packages
只需输入一个符合要求的包（下载时包要正确，卸载时包要存在），即可下载/卸载！  
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/install.png?raw=true)
# cx_feeeze打包
1. 为什么不建议pyinstaller打包？
因为打包工序复杂，并且不支持sv_ttk(会报错)
2. cx_freeze打包  
准备源码，cx_freeze以及python.ico文件
```commandline
pip install cx_freeze
```
输入打包命令  
````commandline
cxfreeze python_tool.py --base-name="win32gui" --icon "python.ico"
````
（代码隐藏控制台）  
打包后如下： 
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/exe.png?raw=true)  
但仅仅这样还不能解决:  
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/ERROR.png?raw=true)  
加入python.ico文件即可  
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/right.png?raw=true)  
成功打包
若有更多问题，请访问[cz_freeze](https://github.com/marcelotduarte/cx_Freeze).
# End
任何人都可以查看那简单的源代码（onefile）[code](https://github.com/githubtohaoyangli/python_tool)
也可以用[pyinstaller](https://github.com/pyinstaller/pyinstaller);[cz_freeze(本人)](https://github.com/marcelotduarte/cx_Freeze)等打包！
但不准商业用途！！！
最后，本软件开发非常活跃，展示图片可能已经过时(2023/12/31：1.3 debug已发布，图片于2024/1/7更新)  
![Image text](https://github.com/githubtohaoyangli/python_tool/blob/main/image/python.ico?raw=true)

