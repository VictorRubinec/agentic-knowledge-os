Dim WshShell, cmd
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Desktop\Anotações"
cmd = Chr(34) & "C:\Users\Rubinec\AppData\Local\Programs\Python\Python313\pythonw.exe" & Chr(34) & " " & Chr(34) & "D:\Desktop\Anotações\scripts\iniciar_automacoes.py" & Chr(34) & " start --all"
WshShell.Run cmd, 0, False
Set WshShell = Nothing
