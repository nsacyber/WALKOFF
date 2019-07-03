.. _prepackaged_apps:

Prepackaged Applications
========================

Hello_World
-----------
	The Hello World app includes simple actions used for testing and as an example/template for app development.


IP_Addr_Utils
-------------
	This is a simple app with an action that converts CIDR notation to a list of IPs. This can be useful for generating lists of IPs to parallelize actions on.


Nmap
----
	This app wraps the Nmap executable. It can run scans and take in the same parameters (hosts and flags) as the regular executable. There are helper functions that can be used for parsing hosts from a host discovery scan, parse scan results for OS fingerprinting, etc.

Power_Shell
-----------
	This app uses PowerShell Remoting Protocol (PSRP) to execute PowerShell scripts on remote Windows hosts. Code can be provided either as .ps1 scripts in the Docker host or as text input on the workflow. Remote hosts must be configured for PowerShell remoting and the corresponding configuration options must be selected on the app.


SSH
---
	This app creates an SSH session to a remote host for executing commands or transferring files over SFTP. As above, bash or other shell scripts can be placed on the Docker host, or commands can be entered in the workflow. The app can also execute commands locally on the Docker container the app is running in.

Walk_Off
--------
	The Walk_Off app provides a demonstration of how to interact with Walkoff's REST API, as well as a more complex example/template for app development.

