taskkill /im msedge.exe /f /t
taskkill /im python3.12.exe /f /t
taskkill /im DriverStation.exe /f /t
cd\Users\Robocubs\Projects\StreamDeck
start /min python3.12 src
cd\Program Files (x86)\Microsoft\Edge\Application
start msedge.exe --hide-crash-restore-bubble http://10.17.1.2:5800/
cd\Program Files (x86)\FRC Driver Station
start DriverStation.exe
