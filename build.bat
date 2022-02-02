cd %~dp0
pyinstaller sortimages_multiview.py --noconfirm
copy .\libglib-2.0-0.dll .\dist\sortimages_multiview\libglib-2.0-0.dll
copy .\libgobject-2.0-0.dll .\dist\sortimages_multiview\libgobject-2.0-0.dll
copy .\libvips-42.dll .\dist\sortimages_multiview\libvips-42.dll
copy .\libvips-cpp-42.dll .\dist\sortimages_multiview\libvips-cpp-42.dll
pause