@echo off
setlocal

:: Set the name of the folder to delete
set "folderToDelete=dist"
set "folderToDelete2=build"
if exist "%folderToDelete%" (
    rmdir /s /q "%folderToDelete%"
    echo Deleted folder: %folderToDelete%
) else (
    echo Folder not found: %folderToDelete%
)
if exist "%folderToDelete2%" (
    rmdir /s /q "%folderToDelete2%"
    echo Deleted folder: %folderToDelete2%
) else (
    echo Folder not found: %folderToDelete2%
)

pyinstaller sortimages_multiview.py --noconfirm

:: Set the name of the file to copy and the destination for the file
set "folderToCopy=vips-dev-8.16"  :: Change this to your actual file name
set "folderCopyDestination=dist\SIME-QOL\_internal\vips-dev-8.16"  :: Change this to your actual destination folder

:::: Copy the folder to the destination folder
if exist "%folderToCopy%" (
    xcopy "%folderToCopy%\*" "%folderCopyDestination%" /s /e /i /y
    echo Copied folder: %folderToCopy% to %folderCopyDestination%
) else (
    echo Folder not found: %folderToCopy%
)

endlocal
pause
