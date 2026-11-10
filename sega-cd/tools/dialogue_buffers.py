"""Expand native resource-report stack buffers for translated strings."""
PATCHES = (
    (0xD160, "4e56ffec", "4e56ff80"),  # 20 -> 128 bytes
    (0xD166, "45eeffec", "45eeff80"),
    (0xD242, "4e56ffd8", "4e56ff80"),  # 40 -> 128; retain two padding bytes
    (0xD24A, "45eeffda", "45eeff82"),
    (0xD292, "4cee0c00ffd0", "4cee0c00ff78"),  # saved A2/A3 move with frame
)

def apply(image, source, files):
    base = files["SMAIN.PRG;1"]["lba"] * 2048
    for offset, before, after in PATCHES:
        old, new = bytes.fromhex(before), bytes.fromhex(after)
        assert source[base+offset:base+offset+len(old)] == old
        image[base+offset:base+offset+len(new)] = new
    return dict(resource_report_bytes=128, patches=[dict(offset=o, before=b, after=a) for o,b,a in PATCHES])
