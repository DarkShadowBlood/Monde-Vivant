# launch_batch.ps1
$batchPath = "C:\important\ApexWear\app web pour apex\app web - Monde Vivant\site web\app web\lancer_site.bat"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$batchPath`"" -Verb RunAs