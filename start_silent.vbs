Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "e:\VsCode\NoteBook"
WshShell.Run "pythonw main.py", 0, False