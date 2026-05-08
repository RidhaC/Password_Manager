Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\ridha\Desktop\Projects\Password_Manager\electron-app"
WshShell.Run "cmd /c npm start", 0, False