import serial, time
ser = serial.Serial(input("Enter serial port to use > "), 115200)

hello_boot = b'!\x07\x90\xcd\x06\x00\xc9Hello World!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00ye'

def reboot():
    ser.read_all()
    ser.write(b"\x01\x01") # send twice to confirm
    c=timeout_read(3)
    while c!=b'\x00':
        ser.write(b"\x01") # send reset command until received
        c=timeout_read(3)
    #printout()
def wr_boot():
    ser.write(b"\xC0")
def timeout_read(timeout = 0.3):
    timer = time.time()+timeout
    while timer>time.time():
        if ser.inWaiting()>0:
            return ser.read()
    return None
def wr_all():
    time.sleep(.1)
    printout()
    ser.write(b'\xC1')
    timer = time.time()+.5
    auth = False
    while timer>time.time() and not auth:
        if ser.inWaiting()>0:
            v = ser.read()
            if v==b'.':
                auth=True
            else:
                print("Command gave bad response:",v, "[continuing anyway]")
                auth = True
    v = timeout_read(5)
    if v==b'k':
        return True
    else:
        print("Command gave bad response: ",v)
        return False
    print("Command timed out!")
    return False
def call_loaded():
    ser.write(b"\x80")
    time.sleep(0.05)
    printout()
    
def send256(buffer):
    printout()
    if type(buffer)==bytes and len(buffer)==256:
        ser.write(b"\x05")
        time.sleep(0.01)
        if(ser.inWaiting()>0):
            print("ERROR: Write failed; Flashing unexpected response!")
            return False
        for i in range(8):
            if(ser.inWaiting()>0):
                printout()
                send256(buffer)
                break
            ser.write(buffer[i:i+1])
            ser.flush()
            time.sleep(0.01)
        for i in range(8,256,8):
            if(ser.inWaiting()>0):
                printout()
                break
            ser.write(buffer[i:i+8])
            ser.flush()
            time.sleep(0.002)
    else:
        print("ERROR: cannot write, invalid buffer!")
        return False
    if timeout_read(.3)!=b'k':
        print("Unknown Error")
        return False
    return True
def make_256(buffer):
    return buffer+bytes(256-len(buffer))
def printout():
    buffer = ser.read_all().replace(b'\x00',b'')
    try:
        print(buffer.decode().replace('\r','\n'), end ='')
    except:
        print(buffer)
def ldexec(fn):
    f = open(fn, 'rb')
    binary = f.read()
    f.close()

    whole_sectors = len(binary)//256

    reboot()

    for i in range(0,whole_sectors*256,256):
        for j in range(10):
            if(send256(binary[i:i+256])):
                break
    send256(make_256(binary[whole_sectors*256:]))

    call_loaded()
def ldburn(fn):
    f = open(fn, 'rb')
    binary = f.read()
    f.close()

    whole_sectors = len(binary)//256

    reboot()

    for i in range(0,whole_sectors*256,256):
        send256(binary[i:i+256])
    send256(make_256(binary[whole_sectors*256:]))

    wr_all()
def testG00nOS(break_fs = False):
    fn = "G00nOS/a.bin"
    f = open(fn, 'rb')
    binary = f.read()
    f.close()

    if break_fs:
        binary = binary+b'\x00'*(4096-len(binary))+bytes([255,255,255,255,255,255])

    whole_sectors = len(binary)//256
    while True:
        reboot()

        time.sleep(4)


        err = False
        for i in range(0,whole_sectors*256,256):
            if not send256(binary[i:i+256]):
                err = True
                break
            time.sleep(0.001)
        if err:
            continue
        if not send256(make_256(binary[whole_sectors*256:])):
            continue
        break
    time.sleep(0.5)

    if(ser.inWaiting()>0):
        print("Error:  System may have rebooted or flash program has glitched.")
        printout()
        return False
    
    wr_all()
    reboot()
    time.sleep(1.2)
    printout()
def clean_hex_table(tbl):
    tbl = tbl.split('\n')[1:]
    for i in range(len(tbl)):
        tbl[i] = tbl[i].split('|')[1]
    return ''.join(tbl)
    
