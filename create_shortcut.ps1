$WshShell = New-Object -ComObject WScript.Shell
$lnkPath = [Environment]::GetFolderPath('Desktop') + '\NoteBook.lnk'
$sc = $WshShell.CreateShortcut($lnkPath)
$sc.TargetPath = 'wscript.exe'
$sc.Arguments = '"e:\VsCode\NoteBook\start_silent.vbs"'
$sc.WorkingDirectory = 'e:\VsCode\NoteBook'
$sc.IconLocation = 'e:\VsCode\NoteBook\icon.ico,0'
$sc.Description = 'NoteBook'
$sc.Hotkey = 'Ctrl+Alt+N'
$sc.WindowStyle = 7
$sc.Save()
Write-Host "Shortcut created: $lnkPath"
Write-Host "Hotkey: Ctrl+Alt+N"