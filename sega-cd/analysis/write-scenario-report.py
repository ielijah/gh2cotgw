from pathlib import Path
import hashlib, json, struct

root = Path(__file__).resolve().parents[1]
out = root / 'analysis/qa-scenarios-final'
names = ['Монголия', 'Гэмпэй', 'Чингисхан', 'Эпоха Юань', 'Покорить мир']
years = [1184, 1180, 1206, 1271, 1185]
rows = []
for i, name in enumerate(names):
    state = (out / f's{i}-final-menu.state').read_bytes()
    byte = lambda a: state[229614 + (a ^ 1)]
    year = byte(0x7fd56) * 256 + byte(0x7fd57)
    season = byte(0x7fd1f)
    pc = struct.unpack_from('<I', state, 1016136)[0]
    assert year == years[i] and season == 3, (i, year, season)
    assert pc in (0x6196, 0x619a), (i, hex(pc))
    rows.append(dict(id=i, name=name, year=year, start_season='весна', end_season='зима', seasonal_transitions=3, cold_boot=True, final_pc=hex(pc), command_menu_responsive=True, screenshot=f's{i}-final-menu.png'))
iso = root / 'build/playable-dub/track01.iso'
report = dict(
    emulator='Genesis Plus GX (libretro)',
    iso_sha256=hashlib.sha256(iso.read_bytes()).hexdigest(),
    iso_bytes=iso.stat().st_size,
    scenarios=rows,
    scope='Default ruler in each scenario; foreign battle visualization disabled through normal menu inputs. No full campaigns or all-ruler coverage. Internal states continue the same cold-boot session; no stale user save states.',
    baseline='Old build crashed in Yuan scenario before winter (PC 0x278); final build reached winter and responsive command menu.',
    confirmed_additional_overflows=['sale 0x2ACF0', 'investment 0x2B8D0', 'troop dispatch 0x2BB64', 'resource dispatch 0x2BCFE'],
    expanded_related_buffers=6,
    validation=['test_command_buffers_cpu.py --strict: 10 cases', 'test_recruitment_buffer_cpu.py: 4 cases', 'test_dialogue_buffers_cpu.py: 18 cases', 'test_event_composition.py', 'verify.py: both CD packages, all audio tracks and preserved assets'],
    command_window_checks='10 controlled native-renderer fixtures in ../qa-command-windows; distinct from ordinary scenario playthrough. Representative longest sale, investment, troop/resource dispatch and alliance windows visually checked: two lines inside frame.',
    packages=['build/playable-dub/game.cue', 'build/playable-japanese-audio/game.cue'],
    preserved='Expanded ISO, generated and original cards, all audio tracks; Mega Drive unchanged.'
)
(out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(rows, ensure_ascii=False, indent=2))
