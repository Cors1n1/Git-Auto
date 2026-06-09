Set objShell = CreateObject("WScript.Shell")
' Executa o python silenciosamente (sem abrir a tela preta do terminal)
objShell.Run "pythonw release.py", 0, False
