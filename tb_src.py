translate_vectors = {
    0x0003:"print",
    0x0006:"println",
    0x0009:"alloc",
    0x000C:"input (BIOS)",
    0x000F:"strcomp",
    0x0012:"chrin",
    0x0015:"chrout",
    0x0018:"print_memory",
    0x001B:"try",
    0x001E:"notry",
    0x0021:"throw",
    0x0024:"traceback",
    0x0028:"strlen",
    0x002B:"blockdevice.read",
    0x002E:"blockdevice.write",
    0x0031:"blockdevice.set_address",
    0x0034:"int_to_hex",
    0x0038:"yield",
    0x003B:"hex_to_int",
    0x003E:"byte_to_hex",
    0x0041:"hex_to_byte",
    0x9000:"BOOT_OFFSET",
    }
f = open(input("OS Binary File > "),'rb')
binary = f.read()
f.close()
tb_list = []
print("Now type in your stack, bottom to top, or most recent call first.  Leave blank to end.")
while True:
    inp = input(" > ")
    if inp=="":
        break
    try:
        tb_list.append(int(inp,16))
    except:
        print("Whoops!  Can't take non-hex '"+inp+"'")
OS_START = 0x9000
OS_END = OS_START + 4096
HEAP_START = 0xA300
HEAP_MAXIMUM = 0xE800
print("Assuming OS is located between "+hex(OS_START)+" and "+hex(OS_END)+'.')

EXACT_MATCH_VECTOR = 0
IN_HEAP = 1
IN_OS = 2
IN_BIOS = 3
IN_ROM = 4
NOT_FOUND = 5

def where_is(offset, can_be_call = True):
    if can_be_call and offset in translate_vectors.keys():
        return [EXACT_MATCH_VECTOR, translate_vectors[offset]]
    if offset<0x8000:
        if offset<0x4000:
            return [IN_BIOS, "[unknown]"]
        else:
            if offset<0x4800:
                return [IN_ROM, "ROM FONT"]
            else:
                return [IN_ROM, "[unknown]"]
    elif offset>=OS_START and offset<OS_END:
        # find matching code, check for call, etc
        return [IN_OS, os_decode_to_str(offset)]
    elif offset>=HEAP_START and offset<HEAP_MAXIMUM:
        return [IN_HEAP, "Heap, "+hex(offset-HEAP_START)]
    return [NOT_FOUND, "[unknown "+hex(offset)+"]"]
def os_decode_to_str(offset):
    # this function disassembles call and jump instructions around the offset.
    offset-= 9 # 9 is 3 bytes for a call, 3 bytes for ld hl, **, and another 3 for ld de, **
    offset-=OS_START # our OS offset is zero, fix the given offset
    b=0

    stro = "Decoded at "+hex(offset+OS_START)+":\n"
    try:
        while b<16:
            cmd = binary[b+offset]
            arg = binary[b+offset+1]|(binary[b+offset+2]<<8)
            stro+=hex(b+offset+OS_START)+" : "
            if cmd==0xCD:
                stro+="CALL   "
            elif cmd==0xC3:
                stro+="JP     "
            elif cmd==0x21:
                stro+="LD HL, "
            elif cmd==0x11:
                stro+="LD DE, "
            elif cmd==0x01:
                stro+="LD BC, "
            elif cmd==0x2A:
                stro+="LD HL,@"
            elif cmd==0x3A:
                stro+="LD A, @"
            else:
                b+=1
                stro+=hex(cmd)+'\n'
                continue
            if arg in translate_vectors.keys():
                stro+=translate_vectors[arg]
            else:
                stro+=hex(arg)
            b+=3
            stro+='\n'
    except:
        pass
    stro+="[end of decode]"
    return stro
collection = []
for i in tb_list:
    collection.append(where_is(i))
collection.reverse()
print("\nMost Recent Call Last:\n")
for i in collection:
    w = i[0]    # location of the pointer
    meta = i[1] # metadata of the pointer
    if w==EXACT_MATCH_VECTOR:
        print("At "+meta)
    elif w==IN_BIOS:
        print("At some point in the bios",meta)
    elif w==IN_ROM:
        pass
    elif w==IN_HEAP:
        print("[Heap :",meta+"]")
    elif w==IN_OS:
        print("In the OS:")
        print(meta)
    elif w==NOT_FOUND:
        print("At an undecodable address: "+meta)
    else:
        print(w,meta)
    
