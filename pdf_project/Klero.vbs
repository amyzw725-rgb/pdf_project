' Launches Streamlit via run_app.bat from this script's folder.
' Window style 1 = visible console (style 0 hid errors - looked like nothing happens).
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
WshShell.Run "cmd /c """ & scriptDir & "\run_app.bat""", 1, False
