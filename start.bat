@echo off
setlocal EnableDelayedExpansion

:: Number of instances to open
set instances=10

:: Loop indefinitely
:loop
    echo Opening %instances% instances of main.py in the background...
    set count=0

    :: Open 5 instances of main.py in the background and store their PIDs
    for /l %%i in (1,1,%instances%) do (
        start /B python main.py
        for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh ^| findstr /i "python.exe"') do (
            set /a count+=1
            set pid[!count!]=%%~a
        )
    )

    echo Waiting for 10 seconds...
    timeout /t 10 >nul

    echo Closing all instances of main.py...
    :: Close all instances of python.exe
    taskkill /im python.exe /f >nul

    echo Restarting the process...
    timeout /t 1 >nul
goto loop