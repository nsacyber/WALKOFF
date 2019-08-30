<#PSScriptInfo

.VERSION 1.0.1

.GUID 4212e294-a195-4cbd-8e61-9c33268b7791

.AUTHOR saw-friendship

.COMPANYNAME

.COPYRIGHT

.TAGS netstat

.LICENSEURI

.PROJECTURI

.ICONURI

.EXTERNALMODULEDEPENDENCIES

.REQUIREDSCRIPTS

.EXTERNALSCRIPTDEPENDENCIES

.RELEASENOTES


.PRIVATEDATA

#>

<#

.DESCRIPTION
 netstat for Windows7/2008R2 like Get-NetTCPConnection with IncludeProcessInfo feature

#>

param (
    [string]$LocalAddress = '*',
    [string]$LocalPort = '*',
    [string]$RemoteAddress = '*',
    [string]$RemotePort = '*',
    [ValidateSet('Closed','Listen','SynSent','SynReceived','Established','FinWait1','FinWait2','CloseWait','Closing','LastAck','TimeWait','DeleteTCB','Bound')][string]$State = '*',
    [string]$OwningProcess = '*',
    [switch]$IncludeProcessInfo
)


if ($IncludeProcessInfo) {
    $Win32_Process = Get-WmiObject -Class Win32_Process | Select-Object -Property @(
        'ProcessName','ProcessId',
        @{Name = 'UserName'; Expression = {$GetOwner = $_.GetOwner(); @{$true = (@($GetOwner.Domain,$GetOwner.User) -join '\')}[$GetOwner.ReturnValue -eq 0]}},
        'Path'
    ) | Group-Object -Property ProcessId -AsHashTable -AsString
}


$StateTable = @{
    'LISTEN' = 'Listen'
    'LISTENING' = 'Listen'
    'SYN_SENT' = 'SynSent'
    'SYN_RECEIVED' = 'SynReceived'
    'ESTABLISHED' = 'Established'
    'CLOSE_WAIT' = 'CloseWait'
    'FIN_WAIT_1' = 'FinWait1'
    'CLOSING' = 'Closing'
    'LAST_ACK' = 'LastAck'
    'CLOSED' = 'Closed'
    'FIN_WAIT_2' = 'FinWait2'
    'TIME_WAIT' = 'TimeWait'
    'Bound' = 'Bound' # wtf?
    'DeleteTCB' = 'DeleteTCB' # wtf?
}

$regex = '\[?([\.\d\:\%a-z]+)\]?\:(\d+)$'

$netstat = (netstat.exe -ano) -split '\n' |
Select-String -Pattern '(\s+[\S]+){5}' |
Select-Object -Skip 1 |
Select-Object -Property @{Name = 'LineArr'; Expression = {$_ -split '\s\s+' -match '\S'}} |
Select-Object -Property @(
    @{Name = 'Protocol'; Expression = {$_.LineArr[0]}},
    @{Name = 'LocalAddress'; Expression = {$_.LineArr[1] -replace @($regex,'$1')}},
    @{Name = 'LocalPort'; Expression = {[UInt32]($_.LineArr[1] -replace @($regex,'$2'))}},
    @{Name = 'RemoteAddress'; Expression = {$_.LineArr[2] -replace @($regex,'$1')}},
    @{Name = 'RemotePort'; Expression = {[UInt32]($_.LineArr[2] -replace @($regex,'$2'))}},
    @{Name = 'State'; Expression = {$StateTable[$_.LineArr[3]]}},
    @{Name = 'OwningProcess'; Expression = {[UInt32]$_.LineArr[4]}}
) | ? {
    ($_.LocalAddress -like $LocalAddress) -and
    ($_.LocalPort -like $LocalPort) -and
    ($_.RemoteAddress -like $RemoteAddress) -and
    ($_.RemotePort -like $RemotePort) -and
    ($_.State -like $State) -and
    ($_.OwningProcess -like $OwningProcess)
}

if (!$IncludeProcessInfo) {
    $netstat
} else {
    $netstat | Select-Object -Property @(
        '*',
        @{Name = 'ProcessName'; Expression = {$Win32_Process[[string]($_.OwningProcess)].ProcessName}},
        @{Name = 'UserName'; Expression = {$Win32_Process[[string]($_.OwningProcess)].UserName}},
        @{Name = 'Path'; Expression = {$Win32_Process[[string]($_.OwningProcess)].Path}}
    )
}