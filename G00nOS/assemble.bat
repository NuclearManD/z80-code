@echo off
:A
tniasm.exe os.z80 a.bin
del tniasm.sym
del tniasm.tmp
pause
goto :A