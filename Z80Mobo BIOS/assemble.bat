@echo off
:A
tniasm.exe BIOS.z80 a.bin
tniasm.exe ROM.z80 rom.bin
del tniasm.sym
del tniasm.tmp
pause
goto :A