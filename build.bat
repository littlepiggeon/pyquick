.\pt\Scripts\activite
python -m nuitka --standalone --no-follow-imports --windows-console-mode=disable --enable-plugins=tk-inter,upx --windows-icon-from-ico=pythontool.ico --upx-binary=D:\upx.exe --show-progress --windows-company-name=p.t. --windows-product-name=python_tool --windows-file-version=1.1.0  --include-data-files=.\pythontool.ico=pythontool.ico --mingw64 --remove-output --run python_tool.py