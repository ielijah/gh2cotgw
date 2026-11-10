"""Expand native resource-report stack buffers for translated strings."""
PATCHES = (
    # Other composed command reports: trade, investment and dispatch.
    (0x1ECF0, "4e56ffe8", "4e56ff80"),
    (0x1ECFE, "49eeffea", "49eeff80"),
    (0x1F008, "4cee3cfcffc0", "4cee3cfcff58"),
    (0x1F012, "4e56ffe4", "4e56ff80"),
    (0x1F01A, "45eeffe6", "45eeff80"),
    (0x1F182, "4cee3c1cffc8", "4cee3c1cff64"),
    (0x1F8D0, "4e56ffe8", "4e56ff80"),
    (0x1F8DC, "47eeffe8", "47eeff80"),
    (0x1F9F2, "4cee1c1cffd0", "4cee1c1cff68"),
    (0x1FB64, "4e56ffdc", "4e56ff80"),
    (0x1FB72, "49eeffdc", "49eeff80"),
    (0x1FCF4, "4cee3c3cffbc", "4cee3c3cff60"),
    (0x1FCFE, "4e56ffdc", "4e56ff80"),
    (0x1FD0C, "49eeffdc", "49eeff80"),
    (0x1FEF8, "4cee3c7cffb8", "4cee3c7cff5c"),
    (0x200D0, "4e56ffd8", "4e56ff80"),
    (0x200DC, "45eeffd8", "45eeff80"),
    (0x2024E, "4cee3c1cffbc", "4cee3c1cff64"),
    # Recruitment command builds a resource prefix + suffix even for AI turns.
    # Keep the other locals at -4..-1; grow its 20-byte string to 124 bytes.
    (0x1F18C, "4e56ffe8", "4e56ff80"),
    (0x1F1A6, "49eeffe8", "49eeff80"),
    (0x1F438, "4cee3cfcffc0", "4cee3cfcff58"),
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
