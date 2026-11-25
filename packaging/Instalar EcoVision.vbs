Option Explicit
Dim shell, fso, source, target, parent, release, shortcut, runtime
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
source = fso.GetParentFolderName(WScript.ScriptFullName)
If Not fso.FileExists(source & "\EcoVision.exe") Then
    MsgBox "Conserva este instalador dentro de la carpeta completa de EcoVision.", 48, "EcoVision"
    WScript.Quit 1
End If
release = "@@APP_VERSION@@"
parent = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs"
If Not fso.FolderExists(parent) Then fso.CreateFolder parent
parent = parent & "\EcoVision"
If Not fso.FolderExists(parent) Then fso.CreateFolder parent
target = parent & "\" & release
If fso.FolderExists(target) Then
    MsgBox "Esta version ya esta instalada en " & target & ". No se sobrescribio.", 64, "EcoVision"
    WScript.Quit 0
End If
runtime = source & "\dependencies\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
If fso.FileExists(runtime) Then
    If shell.Run("""" & runtime & """ /silent /install", 0, True) <> 0 Then
        MsgBox "No se pudo preparar WebView2. Revisa la instalacion antes de continuar.", 48, "EcoVision"
        WScript.Quit 1
    End If
End If
fso.CopyFolder source, target, False
Set shortcut = shell.CreateShortcut(shell.SpecialFolders("Desktop") & "\EcoVision.lnk")
shortcut.TargetPath = target & "\EcoVision.exe"
shortcut.WorkingDirectory = target
shortcut.IconLocation = target & "\EcoVision.exe,0"
shortcut.Save
Set shortcut = shell.CreateShortcut(shell.SpecialFolders("Programs") & "\EcoVision.lnk")
shortcut.TargetPath = target & "\EcoVision.exe"
shortcut.WorkingDirectory = target
shortcut.IconLocation = target & "\EcoVision.exe,0"
shortcut.Save
MsgBox "EcoVision esta instalado. Abre el acceso directo EcoVision del escritorio.", 64, "EcoVision"
