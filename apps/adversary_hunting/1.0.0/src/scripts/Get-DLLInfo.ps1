function Get-TargetCPU {
    [cmdletbinding()]
    param (
        [string]$dllPath
    )
    $mapping = @{}
    $mapping[[System.Reflection.ImageFileMachine]::I386] = "Intel32";
    $mapping[[System.Reflection.ImageFileMachine]::IA64] = "Intel64";
    $mapping[[System.Reflection.ImageFileMachine]::AMD64] = "AMD64";

    $dll = [System.Reflection.Assembly]::LoadFile($dllPath)
    $module = $dll.GetModules($false)[0]
    $imageFileMachine = New-Object -TypeName "System.Reflection.ImageFileMachine"
    $portableExecutableKinds = New-Object -TypeName "System.Reflection.PortableExecutableKinds"
    $module.GetPEKind([ref]$portableExecutableKinds, [ref]$imageFileMachine)
    if ($portableExecutableKinds -eq "ILOnly" -and $imageFileMachine -eq "I386") {
        "AnyCPU"
    }
    else {
        $mapping[$imageFileMachine]
    }
}