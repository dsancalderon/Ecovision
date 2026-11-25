Option Explicit
Dim shell, fso, root, python
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(python) Then
    MsgBox "Falta el entorno de EcoVision. Consulta DESKTOP.md para prepararlo.", 48, "EcoVision"
Else
    shell.CurrentDirectory = root
    shell.Run """" & python & """ """ & root & "\dev_launcher.py""", 0, False
End If
