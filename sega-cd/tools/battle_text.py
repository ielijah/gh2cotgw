"""Russian ordering of surrender reports; both actors retain their original names."""
from text_encoding import encode_stream
TEXTS=[dict(ru='сдался.\nПобедитель:\n')]
def allocate(reserve,put,pairs):
    raw=encode_stream(TEXTS[0]['ru'],pairs)+b'\0'
    text=reserve(len(raw),'battle_surrender_text');put(text,raw)
    helper=reserve(32,'battle_surrender_prefix')
    # Preserve D0/D1/A1, append the predicate, then replay MOVEA of the winner.
    code=bytes.fromhex('48e7c0404879'+f'{0xc000+text:08x}'+'4eb900011ade588f4cdf02032079000655044e75')
    assert len(code)<=32;put(helper,code)
    return dict(helper=helper,text=text,ru=TEXTS[0]['ru'])
def patches(d):
    return [('HEX.PRG;1',0x7c50,'207900065504','4eb9'+f'{0xc000+d["helper"]:08x}')]
def apply(image,source,files,d):
    for file,off,before,after in patches(d):
        a=files[file]['lba']*2048+off;old=bytes.fromhex(before);new=bytes.fromhex(after)
        assert source[a:a+len(old)]==old;image[a:a+len(new)]=new
