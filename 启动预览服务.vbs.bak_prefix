' 盯盘台预览服务常驻 (http.server 8899, 根=D:\股票数据\市场数据\复盘)
' 用途: 本机浏览器预览盯盘台 9 页站点; 服务死后双击此 VBS 或开机自启
Set WshShell = CreateObject("WScript.Shell")
' 检查 8899 是否已被占用(避免重复起)
Dim fso, portFile, isUp
isUp = False
Set fso = CreateObject("Scripting.FileSystemObject")
portFile = "C:\Users\66353\AppData\Local\Temp\preview8899.pid"
If fso.FileExists(portFile) Then
    Dim f, pid
    Set f = fso.OpenTextFile(portFile, 1)
    pid = Trim(f.ReadLine)
    f.Close
    If IsNumeric(pid) And pid > 0 Then
        ' 简单探活: 用 HTTP 请求探测
        Dim http
        Set http = CreateObject("MSXML2.XMLHTTP")
        On Error Resume Next
        http.open "GET", "http://127.0.0.1:8899/", False
        http.send
        If Err.Number = 0 And http.status = 200 Then isUp = True
        On Error GoTo 0
    End If
End If
If Not isUp Then
    ' 以隐藏窗口方式启动 python http.server, 根=复盘目录
    WshShell.Run "cmd /c cd /d D:\股票数据\市场数据\复盘 && python -m http.server 8899 --bind 0.0.0.0", 0, False
    WScript.Sleep 3000
    WScript.Echo "盯盘台预览服务已启动: http://0.0.0.0:8899/盯盘台/index.html (局域网可访问)"
Else
    WScript.Echo "预览服务已在运行 (8899)"
End If
