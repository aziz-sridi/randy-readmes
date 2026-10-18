"""Offline integrity and module-combination checks. Python standard library only."""

import argparse
import base64
from copy import deepcopy
from datetime import date, timedelta
from itertools import combinations
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from generate import ASSETS, ROOT, SVG, STACK_MODULES, ContributionParser, module_duration, palette, render, validate_config, validate_days


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError('Invalid input was accepted')


def check(output, combinations_check=True):
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    snapshot = json.loads((ASSETS / 'contributions.json').read_text(encoding='utf-8'))
    days = snapshot['days']
    validate_days(days)
    assert manifest['username'] == snapshot['username']
    assert manifest['total'] == sum(d['count'] for d in days)
    assert manifest['from'] == days[0]['date'] and manifest['to'] == days[-1]['date']
    assert manifest['duration'] == max(m['duration'] for m in manifest['modules'])
    wanted = {d['date']: d for d in days}
    count = 0
    for module in manifest['modules']:
        skills = module['skills']
        for filename in module['files']:
            path = output / filename
            content = path.read_text(encoding='utf-8')
            assert path.stat().st_size < 5_000_000, 'An SVG exceeds the library size budget'
            root = ET.fromstring(content)
            assert root.attrib['data-module'] == module['id']
            assert int(root.attrib['data-duration']) == module['duration'] == module_duration(module['id'], skills)
            assert root.attrib['viewBox'] == f'0 0 900 {module["height"]}'
            assert root.find(SVG + 'title').text and root.find(SVG + 'desc').text
            cells = [n for n in root.iter() if 'data-date' in n.attrib]
            is_stack = module['id'] in STACK_MODULES
            assert len(cells) == (0 if is_stack else len(days)), 'Wrong calendar content for this section'
            assert {c.attrib['data-date'] for c in cells} == (set() if is_stack else set(wanted))
            if is_stack:
                assert module['section'] == 'Stack'
                assert [node.attrib['data-skill'] for node in root.iter() if 'data-skill' in node.attrib] == [s['name'] for s in skills]
                assert 'real contributions' not in content and 'StackOverflowError' not in content
                assert root.find(SVG + 'title').text == 'Skills Board'
            if module['id'] == 'stack-toolbox':
                assert module['loop'] is True
                animations = [value for value in re.findall(r'animation:[^;}]+', content) if value != 'animation:none!important']
                assert animations and all(' infinite both' in value for value in animations), 'Every board animation must repeat'
                assert 'Adult supervision' not in content
                assert len([node for node in root.iter() if node.attrib.get('data-action') == 'throw-to-screen']) == len(skills)
                assert 'scale(.18)' in content and 'scale(.7)' in content, 'Throws must grow toward the screen'
                assert root.find('.//' + SVG + 'g[@data-prop="skills-board"]') is not None
                categories = list(dict.fromkeys(skill.get('category', 'Stack') for skill in skills))
                assert [node.attrib['data-board-section'] for node in root.iter() if 'data-board-section' in node.attrib] == categories
                assert [node.attrib['data-category'] for node in root.iter() if 'data-skill' in node.attrib] == [skill.get('category', 'Stack') for skill in skills]
            colors = palette(filename.endswith('-dark.svg'))['cells']
            for cell in cells:
                day = wanted[cell.attrib['data-date']]
                assert int(cell.attrib['data-count']) == day['count']
                assert int(cell.attrib['data-level']) == day['level']
                assert cell.attrib['fill'] == colors[day['level']]
            ids = [n.attrib['id'] for n in root.iter() if 'id' in n.attrib]
            assert len(ids) == len(set(ids)), 'SVG IDs must be unique within each file'
            for node in root.iter():
                assert node.tag not in (SVG + 'script', SVG + 'foreignObject')
                assert not any(k.lower().startswith('on') for k in node.attrib)
                href = node.attrib.get('href')
                if href:
                    assert href.startswith(('#', 'data:image/')), 'External image dependency'
                    if href.startswith('#'):
                        assert href[1:] in ids, 'Broken internal SVG reference'
                    else:
                        data = base64.b64decode(href.split(',', 1)[1])
                        assert (data.startswith(b'\x89PNG\r\n\x1a\n') or
                                (data.startswith(b'RIFF') and data[8:12] == b'WEBP'))
            walk = [n for n in root.iter() if n.attrib.get('data-motion') == 'walk']
            assert root.find('.//' + SVG + 'symbol[@id="walking-head"]') is None, 'Whole character frames must replace the head/body assembly'
            assert {int(n.attrib['data-pose']) for n in walk} == {6, 7}
            for frame in walk:
                assert len(frame) == 1 and frame[0].attrib.get('data-part') == 'whole-character', 'A walking frame must be one complete character image'
            if module['id'] == 'tegridy-commits':
                assert 'artist-visibility' not in content, 'Randy must stay visible across the loop'
                assert 'Hand-crafted. Obviously.' not in content
                assert 'A green crayon. A very honest contribution history.' not in content
                sign = root.find('.//' + SVG + 'g[@data-prop="tegridy-sign"]')
                assert sign is not None
                assert [n.text for n in sign.iter(SVG + 'text')] == ['TEGRIDY', 'COMMITS']
                assert all(n.attrib.get('class') == 'tegridy-lettering' for n in sign.iter(SVG + 'text'))
                assert '@font-face{font-family:SouthPark;' in content
                shame = [n for n in root.iter() if n.attrib.get('data-motion') == 'shame']
                assert {int(n.attrib['data-pose']) for n in shame} == {10, 11}
                assert all(len(n) == 1 and n[0].attrib.get('data-part') == 'whole-character' for n in shame)
                assert all(n[0].attrib.get('transform') == 'scale(-1 1)' for n in shame)
                assert not any(word in content for word in ('watering-can', 'water-stream', 'plant-', 'can-tip'))
                assert len([n for n in root.iter() if n.attrib.get('data-ink') == 'fake']) > 0
                assert {int(n.attrib['data-pose']) for n in root.iter() if n.attrib.get('data-motion') == 'draw'} == {8, 9}
                assert root.find('.//' + SVG + 'symbol[@id="weather-cloud"]') is not None
                assert 'stroke-dashoffset:100' in content and 'transform:translateY(48px)' in content
                assert all(n.attrib.get('data-scribble') == 'horizontal' for n in root.iter() if n.attrib.get('data-ink') == 'fake')
                for node in root.iter():
                    if 'data-fake-date' in node.attrib:
                        assert wanted[node.attrib['data-fake-date']]['count'] == 0, 'Crayon touched a real contribution'
            assert '@media(prefers-reduced-motion:reduce)' in content
            assert '.motion{display:none!important}.rest{opacity:1!important}' in content
            assert all(url.startswith(('#', 'data:')) for url in re.findall(r'url\((.*?)\)', content))
            count += 1
    parser = ContributionParser()
    parser.feed('<td id="a" data-date="2026-10-17" data-level="0"></td><td id="b" data-date="2026-10-18" data-level="4"></td>'
                '<tool-tip for="a">No contributions on October 17.</tool-tip><tool-tip for="b">1,234 contributions on October 18.</tool-tip>')
    assert parser.days['a']['count'] == 0 and parser.days['b']['count'] == 1234
    rejected(lambda: validate_days(days[:-50]))
    invalid = deepcopy(days)
    invalid[1]['date'] = invalid[0]['date']
    rejected(lambda: validate_days(invalid))
    invalid = deepcopy(days)
    invalid[0]['level'], invalid[0]['count'] = 0, 1
    rejected(lambda: validate_days(invalid))
    config = json.loads((ROOT / 'randy.json').read_text(encoding='utf-8'))
    invalid_config = deepcopy(config)
    invalid_config['modules'] = ['stack-build']
    rejected(lambda: validate_config(invalid_config))
    for size in (1, 8):
        skills = [dict(config['skills'][i % len(config['skills'])], name='Long skill name'.ljust(24, '!')) for i in range(size)]
        for module in STACK_MODULES:
            root = ET.fromstring(render(module, days, skills))
            assert len([n for n in root.iter() if 'data-skill' in n.attrib]) == size
    root = ET.fromstring(render('stack-toolbox', days, config['toolbox_skills']))
    assert len([n for n in root.iter() if 'data-action' in n.attrib and n.attrib['data-action'] == 'throw-to-screen']) == len(config['toolbox_skills'])
    invalid_config = deepcopy(config)
    invalid_config['toolbox_skills'] = config['toolbox_skills'] * 17
    rejected(lambda: validate_config(invalid_config))
    invalid_config = deepcopy(config)
    invalid_config['toolbox_skills'][0]['category'] = ''
    rejected(lambda: validate_config(invalid_config))
    invalid_config = deepcopy(config)
    invalid_config['skills'][0]['icon'] = '../../outside'
    rejected(lambda: validate_config(invalid_config))
    invalid_config = deepcopy(config)
    invalid_config['username'] = 'bad/user'
    rejected(lambda: validate_config(invalid_config))
    # The daily refresh must handle new years, leap days, and partial weeks.
    for end, length in [(date(2027, 1, 1), 365), (date(2028, 2, 29), 366)]:
        shifted = [dict(days[i % len(days)], date=(end - timedelta(days=length - i - 1)).isoformat())
                   for i in range(length)]
        validate_days(shifted)
        expected = {day['date']: day for day in shifted}
        for module in ('tegridy-commits', 'push-access'):
            root = ET.fromstring(render(module, shifted, config['skills']))
            cells = [node for node in root.iter() if 'data-date' in node.attrib]
            assert len(cells) == length and {node.attrib['data-date'] for node in cells} == set(expected)
            for group in root.iter(SVG + 'g'):
                if len(group) == 1 and 'data-date' in group[0].attrib:
                    when = date.fromisoformat(group[0].attrib['data-date'])
                    assert group.attrib['transform'].endswith(f' {245 + (when.weekday() + 1) % 7 * 16})')
            for node in root.iter():
                if 'data-fake-date' in node.attrib:
                    assert expected[node.attrib['data-fake-date']]['count'] == 0
    combinations_tested = 0
    if combinations_check:
        modules = [m['id'] for m in manifest['modules']]
        with tempfile.TemporaryDirectory(prefix='randy-readme-') as tmp:
            for size in range(1, len(modules) + 1):
                for selected in combinations(modules, size):
                    target = Path(tmp) / str(combinations_tested)
                    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'generate.py'), '--modules', ','.join(selected),
                        '--username', manifest['username'], '--output', str(target)], capture_output=True, text=True)
                    assert result.returncode == 0, result.stderr
                    expected = {m + suffix + '.svg' for m in selected for suffix in ('', '-dark')}
                    assert {f.name for f in target.glob('*.svg')} == expected
                    combo = json.loads((target / 'manifest.json').read_text(encoding='utf-8'))
                    assert [m['id'] for m in combo['modules']] == list(selected)
                    snippet = (target / 'embed.md').read_text(encoding='utf-8')
                    assert snippet.count('<picture>') == size
                    combinations_tested += 1
            for theme in ['light', 'dark']:
                target = Path(tmp) / theme
                result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'generate.py'), '--modules', modules[0],
                    '--username', manifest['username'], '--theme', theme, '--output', str(target)], capture_output=True, text=True)
                assert result.returncode == 0, result.stderr
                assert len(list(target.glob('*.svg'))) == 1
                snippet = (target / 'embed.md').read_text(encoding='utf-8')
                assert '<picture>' not in snippet
    print(f'PASS: {count} self-contained SVGs; {len(days)} exact calendar dates in contribution scenes; skills-only Stack scenes; expanded toolbox and skill limits; parser and input checks; {combinations_tested} module combinations.')


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--output', type=Path, default=ROOT / 'dist')
    args.add_argument('--quick', action='store_true', help='Skip CLI combination checks')
    options = args.parse_args()
    check(options.output, not options.quick)
