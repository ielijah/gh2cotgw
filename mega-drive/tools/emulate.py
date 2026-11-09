"""Headless libretro smoke test with deterministic controller inputs."""
import ctypes as C
from pathlib import Path
import sys, struct, zlib, json
ROOT=Path(__file__).resolve().parents[1]

def png(path,w,h,rgb):
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    data=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))

if __name__=='__main__':
    core=C.CDLL(str(ROOT.parent/'.runtime/emulator/genesis_plus_gx_libretro.dll'))
    ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
    VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
    AUDIO=C.CFUNCTYPE(None,C.c_int16,C.c_int16)
    BATCH=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
    POLL=C.CFUNCTYPE(None)
    INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
    fmt=0; frame=0; captures={}; latest=None
    dirs=str(ROOT.parent/'.runtime').encode(); directory=C.c_char_p(dirs)
    class Var(C.Structure): _fields_=[('key',C.c_char_p),('value',C.c_char_p)]
    @ENV
    def env(cmd,data):
        global fmt
        if cmd in (9,30,31): C.cast(data,C.POINTER(C.c_char_p))[0]=dirs; return True
        if cmd==10: fmt=C.cast(data,C.POINTER(C.c_int))[0]; return True
        if cmd==15: return False
        if cmd==17: C.cast(data,C.POINTER(C.c_bool))[0]=False; return True
        if cmd==18: C.cast(data,C.POINTER(C.c_bool))[0]=True; return True
        if cmd in (16,35,36,37): return True
        return False
    @VIDEO
    def video(ptr,w,h,pitch):
        global latest
        if ptr:
            latest=(C.string_at(ptr,pitch*h),w,h,pitch,fmt)
    @AUDIO
    def audio(l,r): pass
    @BATCH
    def batch(ptr,n): return n
    @POLL
    def poll(): pass
    script=json.loads(sys.argv[3]) if len(sys.argv)>3 else []
    @INPUT
    def inp(port,device,index,key):
        return int(port==0 and any(start<=frame<end and key==button for start,end,button in script))
    for name,cb in [('environment',env),('video_refresh',video),('audio_sample',audio),('audio_sample_batch',batch),('input_poll',poll),('input_state',inp)]:
        getattr(core,'retro_set_'+name)(cb)
    core.retro_init()
    class Game(C.Structure): _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
    rompath=Path(sys.argv[1]).resolve(); content=rompath.read_bytes(); buf=C.create_string_buffer(content)
    game=Game(str(rompath).encode(),C.cast(buf,C.c_void_p),len(content),None)
    core.retro_load_game.argtypes=[C.POINTER(Game)]; core.retro_load_game.restype=C.c_bool
    if not core.retro_load_game(C.byref(game)): raise RuntimeError('load failed')
    for frame in range(int(sys.argv[2])): core.retro_run()
    raw,w,h,pitch,fmt=latest; rgb=bytearray()
    for y in range(h):
        for x in range(w):
            if fmt==1:
                v=int.from_bytes(raw[y*pitch+x*4:y*pitch+x*4+4],'little'); rgb.extend(((v>>16)&255,(v>>8)&255,v&255))
            else:
                v=int.from_bytes(raw[y*pitch+x*2:y*pitch+x*2+2],'little')
                if fmt==2: rgb.extend((((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
                else: rgb.extend((((v>>10)&31)*255//31,((v>>5)&31)*255//31,(v&31)*255//31))
    dest=ROOT/'analysis'/('screen-'+rompath.stem+'.png'); png(dest,w,h,rgb)
    core.retro_get_memory_size.argtypes=[C.c_uint]; core.retro_get_memory_size.restype=C.c_size_t
    core.retro_get_memory_data.argtypes=[C.c_uint]; core.retro_get_memory_data.restype=C.c_void_p
    for memid in (0,2,3):
        size=core.retro_get_memory_size(memid); ptr=core.retro_get_memory_data(memid)
        if ptr and size: (ROOT/'analysis'/f'memory-{memid}.bin').write_bytes(C.string_at(ptr,size))
    print(dest)
    core.retro_unload_game(); core.retro_deinit()
