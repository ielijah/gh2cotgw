"""Use a 20x10 native frame and matching text/selection bounds for the start menu."""
PATCHES = (
    (0x1dd2, '4878000d', '48780001'), # existing frame descriptor 1: 20x10
    (0x1dda, '4878000d', '4878000b'), # left 13 -> 11
    (0x1df4, '4878000e', '4878000c'), # newline origin 14 -> 12 (not width)
    (0x1e02, '4878000e', '4878000c'), # text left 14 -> 12
    (0x1e48, '4878000e', '48780012'), # selection width 14 -> 18
    (0x1e50, '4878000e', '4878000c'), # selection left 14 -> 12
)
# Two tile rows, 32 columns, two bytes per cell: reserve 128 bytes.
MAIN_PATCHES = (
    (0x8a04, '4e56ffc0', '4e56ff80'),
    (0x8a1c, '47eeffc0', '47eeff80'),
    (0x8a98, '4cee0c7cffa4', '4cee0c7cff64'),
)

def prompt_patch(offset):
    # INIT loads at 66000; redirect its only start-menu prompt operand to SMAIN.
    return (0x1dc6, '48790006aeb0', '4879'+f'{0xc000+offset:08x}')

def apply(image, source, files, prompt_offset):
    base=files['INIT.PRG;1']['lba']*2048
    patches = PATCHES + (prompt_patch(prompt_offset),)
    for offset,before,after in patches:
        old=bytes.fromhex(before);new=bytes.fromhex(after)
        assert source[base+offset:base+offset+len(old)]==old
        image[base+offset:base+offset+len(new)]=new
    main_base=files['SMAIN.PRG;1']['lba']*2048
    for offset,before,after in MAIN_PATCHES:
        old=bytes.fromhex(before);new=bytes.fromhex(after)
        assert source[main_base+offset:main_base+offset+len(old)]==old
        image[main_base+offset:main_base+offset+len(new)]=new
    return dict(selection_buffer_bytes=128, selection_max_columns=32,
                selection_patches=[dict(offset=o,before=b,after=a) for o,b,a in MAIN_PATCHES], file='INIT.PRG;1',frame=[11,15,20,10],text_columns=18,
                patches=[dict(offset=o,before=b,after=a) for o,b,a in patches])
