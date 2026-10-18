"""Independent, self-contained Randy README animations. Standard library only.

python scripts/generate.py --refresh
python scripts/generate.py --modules tegridy-commits,push-access
python scripts/generate.py --modules stack-toolbox
"""

import argparse
import base64
import json
import math
import re
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DURATION = 16
DURATIONS = {"tegridy-commits": 19, "push-access": 20, "stack-toolbox": 16}
STACK_MODULES = {"stack-toolbox"}
MODULES = {
    "tegridy-commits": ("Tegridy Commits", "Randy draws fake commits, waits out the rain, and returns to the sign in shame."),
    "push-access": ("Push Access", "Randy presses git push, scattering the contribution calendar."),
    "stack-toolbox": ("Skills Board", "Skills grouped by category."),
}
SVG = "{http://www.w3.org/2000/svg}"


def module_duration(module, skills):
    return max(16, math.ceil(5.3 + (len(skills) - 1) * 1.04)) if module == 'stack-toolbox' else DURATIONS[module]


def module_height(module, skills):
    return max(360, toolbox_layout(skills)[2] + 192) if module == 'stack-toolbox' else 480


def toolbox_layout(skills):
    """Keep category labels and landing positions on the same physical board."""
    groups = {}
    for index, skill in enumerate(skills):
        groups.setdefault(skill.get('category', 'Stack'), []).append(index)
    groups = list(groups.items())
    sections, slots, y = [], {}, 116
    for start in range(0, len(groups), 2):
        pair = groups[start:start + 2]
        row_height = 0
        for column, (name, indices) in enumerate(pair):
            width = 540 if len(pair) == 1 else 260
            columns = min(3, len(indices)) if len(pair) == 1 else 2
            rows = math.ceil(len(indices) / columns)
            height = 68 + (rows - 1) * 40
            x = 306 + column * 280
            block_width = min(176, (width - (columns - 1) * 12) / columns)
            sections.append({'name': name, 'x': x, 'y': y, 'width': width, 'height': height})
            for position, index in enumerate(indices):
                slots[index] = (x + position % columns * (block_width + 12),
                                y + 28 + position // columns * 40, block_width, start + column)
            row_height = max(row_height, height)
        y += row_height + 12
    return sections, slots, y - 12


class ContributionParser(HTMLParser):
    """Pair GitHub calendar cells with their accessible count labels."""

    def __init__(self):
        super().__init__()
        self.days, self.target, self.label = {}, None, ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.days[attrs["id"]] = {
                "date": attrs["data-date"], "level": int(attrs["data-level"])
            }
        if tag == "tool-tip":
            self.target, self.label = attrs.get("for"), ""

    def handle_data(self, value):
        if self.target:
            self.label += value

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            if self.target in self.days:
                match = re.match(r"\s*(No|[\d,]+) contributions? on ", self.label)
                if not match:
                    raise ValueError("GitHub contribution labels changed; saved art was preserved")
                count = match[1]
                self.days[self.target]["count"] = 0 if count == "No" else int(count.replace(",", ""))
            self.target = None


def validate_days(days):
    if not isinstance(days, list) or not 350 <= len(days) <= 372:
        raise ValueError("Expected a complete year of contributions")
    previous = None
    for day in days:
        current = date.fromisoformat(day["date"])
        if previous is not None and current != previous + timedelta(days=1):
            raise ValueError("Calendar dates must be unique and consecutive")
        level, count = day["level"], day["count"]
        if type(level) is not int or type(count) is not int or not 0 <= level <= 4 or count < 0:
            raise ValueError("Invalid contribution level or count")
        if (level == 0) != (count == 0):
            raise ValueError("Contribution level and count disagree")
        previous = current


def validate_config(config):
    username = config.get("username", "")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
        raise ValueError("Use a valid GitHub username")
    modules = config.get("modules", [])
    if not modules or len(set(modules)) != len(modules) or any(m not in MODULES for m in modules):
        raise ValueError("Choose unique modules: " + ", ".join(MODULES))
    validate_skills(config.get('skills', []), 16 if modules == ['stack-toolbox'] else 8)
    if 'toolbox_skills' in config:
        validate_skills(config['toolbox_skills'], 16)


def validate_skills(skills, limit):
    if not isinstance(skills, list) or not 1 <= len(skills) <= limit:
        raise ValueError(f"Choose between one and {limit} skills")
    for skill in skills:
        if not isinstance(skill.get("name"), str) or not 1 <= len(skill["name"].strip()) <= 24:
            raise ValueError("Skill names must contain 1 to 24 characters")
        if not re.fullmatch(r"[a-z0-9-]+", skill.get("icon", "")):
            raise ValueError("Skill icon must be the name of a local assets/icons SVG")
        if not (ASSETS / "icons" / (skill["icon"] + ".svg")).is_file():
            raise ValueError("Missing skill icon: " + skill["icon"])
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", skill.get("color", "")):
            raise ValueError("Skill colors must be six-digit hex values")
        if 'category' in skill and (not isinstance(skill['category'], str) or not 1 <= len(skill['category'].strip()) <= 32):
            raise ValueError('Skill categories must contain 1 to 32 characters')


def fetch_days(username):
    # ponytail: public HTML avoids secrets; use GraphQL if GitHub changes its calendar markup.
    request = Request(f"https://github.com/users/{username}/contributions", headers={
        "User-Agent": "randy-readme", "Accept-Language": "en-US"
    })
    with urlopen(request, timeout=30) as response:
        parser = ContributionParser()
        parser.feed(response.read().decode("utf-8"))
    days = sorted(parser.days.values(), key=lambda day: day["date"])
    validate_days(days)
    return days


def palette(dark):
    return ({"paper": "#101a22", "ink": "#edeae0", "muted": "#a9b8bf", "line": "#344951",
             "ground": "#20382f", "green": "#a1d086", "yellow": "#efc75b", "red": "#f09480",
             "cells": ["#23333d", "#164932", "#237445", "#3aa95c", "#8bd77b"]}
            if dark else
            {"paper": "#f7f5eb", "ink": "#202c30", "muted": "#586b6d", "line": "#c5d1c7",
             "ground": "#dfe9d0", "green": "#397142", "yellow": "#c99524", "red": "#b54d37",
             "cells": ["#e1e7dd", "#a7d895", "#6db86b", "#398b4d", "#246038"]})


def cycle(start, end, poses, fps=16):
    """Frame windows on the shared clock, with no blank frames between steps."""
    result, beat = [], start
    while beat < end:
        stop = min(end, beat + 100 / (DURATION * fps))
        result.append((poses[len(result) % len(poses)], round(beat, 3), round(stop - .01, 3)))
        beat = stop
    return result


def walking(start, end):
    return cycle(start, end, (6, 7), fps=4)


class Scene:
    """One SVG with a shared clock, embedded art, and an accessible still frame."""

    def __init__(self, module, days, skills, dark, username):
        self.module, self.days, self.skills, self.p = module, days, skills, palette(dark)
        self.duration = module_duration(module, skills)
        self.end = 100 if self.duration == DURATION else 100 * self.duration / DURATION
        self.styles, self.parts, self.serial = [], [], 0
        self.dark, self.username = dark, username
        self.height = module_height(module, skills)
        start = date.fromisoformat(days[0]["date"])
        self.sunday = start - timedelta(days=(start.weekday() + 1) % 7)
        self.columns = (date.fromisoformat(days[-1]["date"]) - self.sunday).days // 7 + 1
        self.pitch = 617 / self.columns

    def add(self, value):
        self.parts.append(value)

    def animate(self, name, frames, base="", easing="linear"):
        # Keep the original 16-second story clock; extra time extends the ending.
        if self.duration != DURATION:
            frames = [(round(percent * DURATION / self.duration, 6), state) for percent, state in frames]
        self.styles.append(f".{name}{{{base};animation:{name} {self.duration}s {easing} infinite both}}")
        self.styles.append("@keyframes " + name + "{" + "".join(
            f"{percent}%{{{state}}}" for percent, state in frames
        ) + "}")

    def visible(self, name, start, end, still=False, property="opacity"):
        hidden = f'{property}:' + ('hidden' if property == 'visibility' else '0')
        shown = f'{property}:' + ('visible' if property == 'visibility' else '1')
        frames = [(0, hidden)]
        if start:
            frames.append((max(0, start - .01), hidden))
        frames.extend([(start, shown), (end, shown)])
        if self.module != 'stack-toolbox' or end < self.end:
            frames.extend([(min(self.end, end + .01), hidden), (self.end, hidden)])
        self.animate(name, frames, shown if still else hidden, "steps(1,end)")

    def text(self, x, y, value, size=16, extra=""):
        return f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(value))}</text>'

    def caption(self, name, value, start, end, color=None):
        self.visible(name, start, end, still=start == 0)
        self.add(f'<g class="{name} {"rest" if start == 0 else "motion"}">' +
                 self.text(860, 125, value, 22,
                           f'text-anchor="end" font-weight="700" fill="{color or self.p["ink"]}"') + '</g>')

    def coord(self, day):
        col, row = divmod((date.fromisoformat(day["date"]) - self.sunday).days, 7)
        return 235 + col * self.pitch, 245 + row * 16

    def calendar(self, effect=""):
        result = '<g class="calendar" aria-label="Real contribution calendar">'
        month = None
        for day in self.days:
            x, y = self.coord(day)
            when = date.fromisoformat(day["date"])
            row = (when.weekday() + 1) % 7
            if (month is None or row == 0) and when.month != month and x < 825:
                label_class = 'muted mono'
                if effect == 'explode':
                    label = 'blast-month-' + when.isoformat()
                    restore = 91 + (x - 235) / self.pitch * .20
                    self.animate(label, [(0, 'opacity:1'), (35, 'opacity:1'), (38, 'opacity:0'),
                        (round(restore + 2.5, 3), 'opacity:0'), (round(restore + 4.5, 3), 'opacity:1'),
                        (self.end, 'opacity:1')], 'opacity:1')
                    label_class += ' ' + label
                result += self.text(round(x, 2), 232, when.strftime("%b"), 10, f'class="{label_class}"')
                month = when.month
            extra = ""
            if effect == 'explode':
                index = (when - self.sunday).days
                name = 'blast-tile-' + when.isoformat()
                landing_x = 404 + index * 73 % 441 - x
                landing_y = 373 + index * 17 % 21 - y
                distance = ((x - 340) ** 2 + (y - 250) ** 2) ** .5
                launch = 35 + distance / 620 * 3.2 + index % 7 * .025
                flight = 7.5 + index * 29 % 41 / 10
                lift = 64 + (index * 47 + index // 7 * 19) % 109
                kick = (x - 340) / max(120, distance) * (26 + index * 7 % 39)
                spin = (index % 9 - 4) * 74 + (360 if index % 2 else -360)
                frames = [(0, 'opacity:1;transform:none'), (round(launch, 3), 'opacity:1;transform:none')]
                # Sample a gravity arc so each paper square has its own launch and landing.
                for step in range(1, 11):
                    t = step / 10
                    dx = max(30 - x, min(862 - x, landing_x * t + kick * 4 * t * (1 - t)))
                    dy = landing_y * t - lift * 4 * t * (1 - t)
                    frames.append((round(launch + flight * t, 3),
                        f'opacity:1;transform:translate({dx:.2f}px,{dy:.2f}px) rotate({spin * t:.2f}deg)'))
                ground = f'transform:translate({landing_x:.2f}px,{landing_y}px) rotate({spin}deg)'
                restore = 91 + (index // 7) * .20 + row * .08
                # Fade rubble in place, then settle each column into its real dates.
                frames += [(round(restore, 3), 'opacity:1;' + ground),
                    (round(restore + 1.2, 3), 'opacity:0;' + ground),
                    (round(restore + 1.21, 3), 'opacity:0;transform:translateY(12px)'),
                    (round(restore + 1.6, 3), 'opacity:0;transform:translateY(12px);animation-timing-function:cubic-bezier(.22,1,.36,1)'),
                    (round(restore + 3.5, 3), 'opacity:1;transform:none'),
                    (self.end, 'opacity:1;transform:none')]
                self.animate(name, frames, 'opacity:1;transform-box:fill-box;transform-origin:center')
                extra = f' class="{name}" data-effect="explode"'
            result += (f'<g transform="translate({x:.3f} {y})"><rect{extra} data-date="{day["date"]}" '
                       f'data-count="{day["count"]}" data-level="{day["level"]}" width="{self.pitch - 2.8:.3f}" '
                       f'height="12" rx="1.8" fill="{self.p["cells"][day["level"]]}" stroke="{self.p["line"]}" stroke-width=".35">'
                       f'<title>{day["date"]}: {day["count"]} contributions</title></rect></g>')
        return result + '</g>'

    def pose(self, index, size=180):
        # Atlas cells include transparent margins. The local origin is the feet.
        position = f'x="{-size / 2}" y="{-size * 490 / 512}" width="{size}" height="{size}"'
        if index >= 6:
            name, frame = ('shame', index - 10) if index >= 10 else ('motion', index - 6)
            motion = json.loads((ASSETS / 'randy' / (name + '.json')).read_text(encoding='utf-8'))
            anchor, cell = motion['anchors'][frame], motion['cells'][frame]
            position = f'x="{-anchor["x"] * size / cell[2]:.4f}" y="{-anchor["y"] * size / cell[3]:.4f}" width="{size}" height="{size}"'
            if index >= 10:
                position += ' transform="scale(-1 1)"'
            return f'<use href="#{name}-{frame}" {position} data-part="whole-character"/>'
        return f'<use href="#pose-{index}" {position}/>'

    def actor(self, poses, size=180, seamless=False):
        result = ""
        for i, (pose, start, end) in enumerate(poses):
            name = f"actor-{self.serial}-{i}"
            if seamless:
                end = self.end if self.module == 'stack-toolbox' and i == len(poses) - 1 else round((poses[i + 1][1] if i + 1 < len(poses) else self.end) - .01, 3)
            self.visible(name, start, end, still=i == 0, property="visibility")
            kind = 'shame' if pose >= 10 else 'draw' if pose >= 8 else 'walk' if pose >= 6 else 'expression'
            result += f'<g class="{name} {"rest" if i == 0 else "motion"}" data-pose="{pose}" data-motion="{kind}">{self.pose(pose, size)}</g>'
        self.serial += 1
        return result

    def icon(self, skill, x, y, size=22):
        return f'<use href="#icon-{skill["icon"]}" x="{x}" y="{y}" width="{size}" height="{size}" fill="{skill["color"]}"/>'

    def block(self, skill, width=116, height=32, color="#efcb70"):
        studs = ''.join(f'<rect x="{x}" y="-4" width="14" height="6" rx="1" fill="{color}" stroke="#283437" stroke-width="1.6"/>' for x in (16, width - 30))
        return (studs + f'<rect width="{width}" height="{height}" rx="3" fill="{color}" stroke="#283437" stroke-width="2"/>' +
                self.icon(skill, 8, (height - min(22, height - 6)) / 2, min(22, height - 6)) +
                self.text(36, height / 2 + 4, skill["name"], min(13, (width - 42) / (len(skill["name"]) * .58)),
                          'font-weight="700" fill="#283437"'))

    def finish(self):
        title, subtitle = MODULES[self.module]
        total = sum(day["count"] for day in self.days)
        description = (f'{subtitle} Kid Randy Marsh stars in a {self.duration}-second loop. '
                       + ('The calendar explodes when he presses git push. Randy flips through the air, falls, gets up, '
                          'and holds a Works on my machine sign. ' if self.module == 'push-access' else '') +
                       f'{self.username}: {total:,} real contributions, {self.days[0]["date"]} to {self.days[-1]["date"]}. '
                       'Every contribution square returns to its exact date and intensity. Skills: ' +
                       ', '.join(skill['name'] for skill in self.skills) + '. Reduced motion displays the original calendar.')
        is_stack = self.module in STACK_MODULES
        if is_stack:
            description = (f'{title}. Kid Randy Marsh throws technology blocks into labeled sections of a wooden skills board. '
                           f'The completed board holds briefly before the {self.duration}-second loop repeats. Skills: ' +
                           ', '.join(skill['name'] for skill in self.skills) +
                           '. Reduced motion shows every skill in its finished position. No contribution calendar.')
        atlas = json.loads((ASSETS / "randy" / "atlas.json").read_text(encoding="utf-8"))
        encoded = base64.b64encode((ASSETS / "randy" / atlas["file"]).read_bytes()).decode("ascii")
        defs = f'<image id="randy-atlas" width="{atlas["width"]}" height="{atlas["height"]}" href="data:{atlas["mime"]};base64,{encoded}"/>'
        for i, box in enumerate(atlas["cells"]):
            defs += f'<symbol id="pose-{i}" viewBox="{" ".join(str(n) for n in box)}" overflow="hidden"><use href="#randy-atlas"/></symbol>'
        motion = json.loads((ASSETS / 'randy' / 'motion.json').read_text(encoding='utf-8'))
        encoded = base64.b64encode((ASSETS / 'randy' / motion['file']).read_bytes()).decode('ascii')
        defs += f'<image id="motion-atlas" width="{motion["width"]}" height="{motion["height"]}" href="data:{motion["mime"]};base64,{encoded}"/>'
        for i, box in enumerate(motion['cells']):
            defs += (f'<symbol id="motion-{i}" viewBox="{" ".join(str(n) for n in box)}" overflow="hidden">'
                     '<use href="#motion-atlas"/></symbol>')
        if self.module == 'tegridy-commits':
            shame = json.loads((ASSETS / 'randy' / 'shame.json').read_text(encoding='utf-8'))
            encoded = base64.b64encode((ASSETS / 'randy' / shame['file']).read_bytes()).decode('ascii')
            defs += f'<image id="shame-atlas" width="{shame["width"]}" height="{shame["height"]}" href="data:{shame["mime"]};base64,{encoded}"/>'
            for i, box in enumerate(shame['cells']):
                defs += (f'<symbol id="shame-{i}" viewBox="{" ".join(str(n) for n in box)}" overflow="hidden">'
                         '<use href="#shame-atlas"/></symbol>')
            cloud = ET.parse(ASSETS / 'weather' / 'openmoji-cloud.svg').getroot()
            paths = ''.join('<path ' + ' '.join(f'{k}="{escape(v, quote=True)}"' for k, v in node.attrib.items()) + '/>'
                            for node in cloud.iter(SVG + 'path'))
            defs += '<symbol id="weather-cloud" viewBox="4 15 64 42">' + paths + '</symbol>'
        for icon in sorted({s['icon'] for s in self.skills}):
            root = ET.parse(ASSETS / "icons" / f"{icon}.svg").getroot()
            paths = ''.join(f'<path d="{escape(n.attrib["d"], quote=True)}"/>' for n in root.iter(SVG + "path"))
            if not paths:
                raise ValueError("Icon contains no paths: " + icon)
            defs += f'<symbol id="icon-{icon}" viewBox="{root.attrib.get("viewBox", "0 0 24 24")}">{paths}</symbol>'
        p = self.p
        legend = ''.join(f'<rect x="{750 + i * 15}" y="445" width="10" height="10" rx="2" fill="{c}"/>' for i, c in enumerate(p['cells']))
        font = base64.b64encode((ASSETS / 'fonts' / 'LilitaOne-Regular.ttf').read_bytes()).decode('ascii')
        sign_font = ''
        if self.module == 'tegridy-commits':
            encoded = base64.b64encode((ASSETS / 'fonts' / 'SouthPark.ttf').read_bytes()).decode('ascii')
            sign_font = (f'@font-face{{font-family:SouthPark;src:url(data:font/ttf;base64,{encoded})}}'
                         '.tegridy-lettering{font-family:SouthPark,Lilita,sans-serif;font-weight:400}')
        header = '' if is_stack else (
            self.text(864, 44, f'{total:,}', 24, 'font-weight="900" text-anchor="end"') +
            self.text(864, 65, 'real contributions', 11, 'class="muted" text-anchor="end"'))
        footer = (self.text(864, self.height - 29, f'{len(self.skills)} technologies', 11,
                           'class="muted" text-anchor="end"') if is_stack else
                  self.text(450, 451, f'{self.days[0]["date"]} / {self.days[-1]["date"]}', 11, 'class="mono muted" text-anchor="middle"') +
                  self.text(738, 454, 'Less', 10, 'class="muted" text-anchor="end"') + legend +
                  self.text(832, 454, 'More', 10, 'class="muted"'))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{self.height}" viewBox="0 0 900 {self.height}" role="img" '
                f'aria-labelledby="title description" data-module="{self.module}" data-duration="{self.duration}">'
                f'<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>'
                '<metadata>Unofficial South Park fan art. Randy Marsh belongs to the South Park rights holders. '
                'Character poses generated from the user-supplied reference. Icons: Simple Icons, CC0. '
                'Cloud artwork by OpenMoji, CC BY-SA 4.0. See CREDITS.md.</metadata>'
                f'<defs>{defs}<clipPath id="stage"><rect x="20" y="84" width="860" height="{self.height - 145}"/></clipPath></defs>'
                f'<style>@font-face{{font-family:Lilita;src:url(data:font/ttf;base64,{font})}}' + sign_font +
                'text{font-family:"Trebuchet MS",Arial,sans-serif}svg{isolation:isolate}'
                f'svg{{fill:{p["ink"]}}}.muted{{fill:{p["muted"]}}}.mono{{font-family:Consolas,"Liberation Mono",monospace}}'
                '.display{font-family:Lilita,"Trebuchet MS",sans-serif;font-weight:400}'
                'use{pointer-events:none}' + ''.join(self.styles) +
                '@media(prefers-reduced-motion:reduce){*{animation:none!important}.motion{display:none!important}.rest{opacity:1!important}}'
                '</style>'
                f'<rect x="1" y="1" width="898" height="{self.height - 2}" rx="14" fill="{p["paper"]}" stroke="{p["line"]}" stroke-width="2"/>'
                + self.text(30, 47, 'Stack' if is_stack else title, 36, 'class="display"')
                + (self.text(32, 70, subtitle, 13, 'class="muted"') if self.module != 'tegridy-commits' else '')
                + header
                + f'<g clip-path="url(#stage)"><path d="M20 {self.height - 80}H880V{self.height - 60}H20Z" fill="{p["ground"]}"/>'
                + f'<path d="M28 {self.height - 80}H872" stroke="{p["line"]}" stroke-width="2"/>'
                + ''.join(self.parts) + '</g>'
                + self.text(31, self.height - 29, '@' + self.username, 12, 'class="mono muted"')
                + footer + '</svg>\n')


def garden(s):
    p = s.p
    s.caption('garden-setup', 'Just a few finishing touches.', 0, 40)
    s.caption('garden-lie', '100% organic contributions.', 40.01, 56, p['green'])
    s.caption('garden-rain-caption', 'Wait. Those were permanent.', 56.01, 71)
    s.caption('garden-end', 'Must be a GitHub bug.', 71.01, 107.25)
    s.caption('garden-reset', 'Just a few finishing touches.', 107.26, s.end - .01)
    s.add('<g data-prop="tegridy-sign" transform="translate(38 153) rotate(-3 86 42)">'
          '<path d="M80 76L77 246H89L91 76Z" fill="#9c7951" stroke="#705337" stroke-width="2"/>'
          '<path d="M85 91L83 236" stroke="#bd9766" stroke-width="2"/>'
          '<path d="M3 3L170 0L173 40L1 43Z" fill="#e8c47d" stroke="#705337" stroke-width="2.5" stroke-linejoin="round"/>'
          '<path d="M1 46L172 43L169 83L4 86Z" fill="#deba72" stroke="#705337" stroke-width="2.5" stroke-linejoin="round"/>'
          '<path d="M10 8L160 5M12 78L158 75M5 31L17 30M154 54L167 53" fill="none" stroke="#b78c4e" stroke-width="1.4" stroke-linecap="round"/>'
          '<g fill="#705337"><circle cx="11" cy="20" r="2.1"/><circle cx="162" cy="18" r="2.1"/>'
          '<circle cx="12" cy="62" r="2.1"/><circle cx="160" cy="60" r="2.1"/></g>' +
          s.text(86, 32, 'TEGRIDY', 28, 'class="tegridy-lettering" text-anchor="middle" fill="#3e492e"') +
          s.text(86, 74, 'COMMITS', 26, 'class="tegridy-lettering" text-anchor="middle" fill="#493c2a"') + '</g>')
    s.add(s.calendar())
    empty = [d for d in s.days if d['count'] == 0 and s.coord(d)[1] >= 309]
    nearby = sorted({s.coord(d)[0] for d in empty if 450 < s.coord(d)[0] < 540})
    columns = (nearby or sorted({s.coord(d)[0] for d in empty}))[:6] or [495]
    lo, hi = min(columns) - s.pitch, max(columns) + s.pitch * 2
    blanks = [d for d in s.days if d['count'] == 0 and s.coord(d)[0] in columns and s.coord(d)[1] >= 309]
    clip = ''.join(f'<rect x="{s.coord(d)[0]:.3f}" y="{s.coord(d)[1]}" width="{s.pitch - 2.8:.3f}" height="12" rx="1.8" data-fake-date="{d["date"]}"/>' for d in blanks)
    s.add('<defs><clipPath id="blank-squares">' + clip + '</clipPath></defs>')
    # Walk from the sign to an earlier part of the year, drawing from 3.2 seconds.
    poses = [(0, 0, 1)] + walking(1.01, 20)
    positions = [(0, 'transform:none'), (1, 'transform:none')]
    period = 20 / len(columns)
    for i, x in enumerate(columns):
        start = 20 + i * period
        finish = start + period - .6
        actor_x = x + (s.pitch - 2.8) / 2 - 78
        positions += [(round(start, 3), f'transform:translate({actor_x - 105:.3f}px,0)'),
                      (round(finish, 3), f'transform:translate({actor_x - 105:.3f}px,0)')]
        poses += cycle(start, finish, (8, 9), fps=6)
        if i < len(columns) - 1:
            poses += walking(finish + .01, start + period)
        # Restore the original three short horizontal crayon strokes in each square.
        segments = []
        for day in blanks:
            px, py = s.coord(day)
            if abs(px - x) < .01:
                length = s.pitch - 5
                segments.append(f'M{px + 1:.3f} {py + 3}l{length:.3f} 1m-{length:.3f} 3l{length:.3f} 1m-{length:.3f} 3h{length:.3f}')
        path = ''.join(segments)
        name = f'fake-ink-{i}'
        s.animate(name, [(0, 'opacity:0;stroke-dashoffset:100'),
            (round(start, 3), 'opacity:1;stroke-dashoffset:100'),
            (round(finish, 3), 'opacity:1;stroke-dashoffset:0'),
            (67, 'opacity:1;stroke-dashoffset:0'), (69, 'opacity:0;stroke-dashoffset:0'),
            (99.99, 'opacity:0;stroke-dashoffset:0'), (100, 'opacity:0;stroke-dashoffset:100')],
            'opacity:0;stroke-dasharray:100;stroke-dashoffset:100')
        wash = f'wash-{i}'
        s.animate(wash, [(0, 'transform:none'), (round(55 + i * .12, 3), 'transform:none'),
                        (round(64 + i * .12, 3), 'transform:translateY(48px)'),
                        (99.99, 'transform:translateY(48px)'), (100, 'transform:none')])
        s.add(f'<defs><clipPath id="wash-area-{i}"><rect class="{wash}" x="{x - 1:.3f}" y="307" width="{s.pitch + 2:.3f}" height="49"/></clipPath></defs>'
              f'<g class="motion" clip-path="url(#blank-squares)"><g clip-path="url(#wash-area-{i})">'
              f'<path class="{name}" d="{path}" pathLength="100" fill="none" stroke="{p["cells"][3]}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" data-ink="fake" data-scribble="horizontal"/>'
              '</g></g>')
    aside = actor_x - 105 - 75
    # He notices the rain after 0.96 seconds, waits it out, then returns to the sign.
    positions += [(47, f'transform:translate({aside:.3f}px,0)'),
                  (74, f'transform:translate({aside:.3f}px,0)'),
                  (96, 'transform:none'), (100, 'transform:none')]
    last = 40 - .6
    poses += (walking(last + .01, 47) + [(5, 47.01, 56), (4, 56.01, 71), (10, 71.01, 74)] +
              cycle(74.01, 96, (10, 11), fps=2.5) + [(10, 96.01, 107.25), (0, 107.26, s.end - .01)])
    s.animate('artist', positions)
    s.add('<g transform="translate(105 400)"><g class="artist">' +
          s.actor(poses, seamless=True) + '</g></g>')
    s.visible('rain-cloud', 45, 69)
    cloud_x = min(735, (lo + hi) / 2 - 65)
    s.animate('cloud-arrival', [(0, 'transform:translateX(65px)'), (45, 'transform:translateX(65px)'),
                               (50, 'transform:none'), (100, 'transform:none')])
    s.add(f'<g class="rain-cloud motion" transform="translate({cloud_x:.3f} 130)"><g class="cloud-arrival">'
          '<use href="#weather-cloud" width="150" height="82" data-source="OpenMoji 2601"/>'
          '</g></g>')
    for i in range(22):
        name = f'rain-{i}'
        x = lo - 8 + i * (hi - lo + 26) / 21
        frames = [(0, 'opacity:0;transform:none')]
        for j in range(6):
            beat = 50 + i % 5 * .3 + j * 2.5
            frames += [(round(beat, 3), 'opacity:0;transform:none'),
                       (round(beat + .01, 3), 'opacity:.85;transform:none'),
                       (round(beat + 2.15, 3), 'opacity:.65;transform:translate(-8px,157px)'),
                       (round(beat + 2.2, 3), 'opacity:0;transform:translate(-8px,157px)')]
        frames.append((100, 'opacity:0;transform:none'))
        s.animate(name, frames, 'opacity:0')
        s.add(f'<path class="{name} motion" d="M{x:.3f} 210l-2 10" fill="none" stroke="#70a5c7" stroke-width="2" stroke-linecap="round"/>')


def push(s):
    p = s.p
    s.caption('push-setup', 'Seems pretty self-explanatory.', 0, 29)
    s.caption('push-command', '$ git push --force', 29.01, 47, p['red'])
    s.caption('push-blame', '$ git blame  >  randy', 47.01, s.end)
    s.add(s.calendar('explode'))
    s.animate('push-blast', [(0, 'opacity:0;transform:scale(.25)'),
        (35, 'opacity:0;transform:scale(.25)'), (35.01, 'opacity:1;transform:scale(.25)'),
        (38, 'opacity:1;transform:scale(1)'), (42, 'opacity:0;transform:scale(1.2)'),
        (100, 'opacity:0;transform:scale(1.2)')], 'opacity:0')
    s.add('<g transform="translate(340 250)"><g class="push-blast motion" data-prop="explosion">'
          '<path d="M-26-40L-14-92 13-49 54-80 48-28 101-21 58 10 85 56 33 44 18 88-9 49-60 73-49 24-99 4-48-16-77-61Z" fill="#d86149" stroke="#853e31" stroke-width="3"/>'
          '<path d="M-15-25L-4-58 14-25 42-42 32-9 65 3 32 17 36 48 8 30-11 57-21 25-51 28-33 5-58-15Z" fill="#efcb70"/>'
          '</g></g>')
    for i, skill in enumerate(s.skills[:3]):
        s.add(f'<g transform="translate({135 + i * 64} {368 - i * 34})">' + s.block(skill, 88, 32,
              ['#e8c76b', '#8eb7c2', '#a6bb8b'][i]) + '</g>')
    s.add('<g data-prop="push-button-housing">'
          '<path d="M340 264V400" stroke="#697573" stroke-width="7"/>'
          '<path d="M296 223L383 222 384 267 297 268Z" fill="#576663" stroke="#283437" stroke-width="2.5" stroke-linejoin="round"/></g>')
    s.animate('push-button', [(0, 'transform:none'), (32, 'transform:none'), (35, 'transform:translateY(7px)'),
                            (41, 'transform:translateY(7px)'), (45, 'transform:none'), (100, 'transform:none')])
    s.add('<g class="push-button" data-prop="push-button-cap">'
          '<path d="M302 219L377 218 378 255 303 256Z" fill="#80574d" stroke="#4b3832" stroke-width="2" stroke-linejoin="round"/>'
          '<path d="M302 214L377 215 378 249 303 250Z" fill="#b97563" stroke="#4b3832" stroke-width="2" stroke-linejoin="round"/>' +
          s.text(340, 237, 'git push', 16, 'class="display" fill="#f1e7cf" text-anchor="middle"') + '</g>')
    s.animate('pusher', [(0, 'transform:none'), (9, 'transform:none'), (17, 'transform:translate(75px,-32px)'),
        (23, 'transform:translate(139px,-66px)'), (29, 'transform:translate(185px,-100px)'),
        (35, 'transform:translate(185px,-100px)'), (38, 'transform:translate(275px,-135px)'),
        (41, 'transform:translate(375px,-120px)'), (44, 'transform:translate(470px,-55px)'),
        (47, 'transform:translate(560px,12px)'), (54, 'transform:translate(560px,12px)'),
        (60, 'transform:translate(560px,0)'), (87, 'transform:translate(560px,0)'),
        (120, 'transform:none'), (s.end, 'transform:none')])
    s.animate('randy-flip', [(0, 'transform:rotate(0deg)'), (35, 'transform:rotate(0deg)'),
        (38, 'transform:rotate(120deg)'), (41, 'transform:rotate(240deg)'),
        (44, 'transform:rotate(330deg)'), (47, 'transform:rotate(450deg)'),
        (54, 'transform:rotate(450deg)'), (60, 'transform:rotate(360deg)'),
        (87, 'transform:rotate(360deg)'), (87.01, 'transform:rotate(0deg)'),
        (100, 'transform:rotate(0deg)')])
    s.animate('randy-facing', [(0, 'transform:scaleX(1)'), (86.99, 'transform:scaleX(1)'),
        (87, 'transform:scaleX(-1)'), (119.99, 'transform:scaleX(-1)'),
        (120, 'transform:scaleX(1)'), (s.end, 'transform:scaleX(1)')],
        'transform:scaleX(1)', 'steps(1,end)')
    s.visible('machine-sign', 67.5, 86.99)
    sign = ('<g class="machine-sign motion" data-prop="machine-sign">'
            '<path d="M69-105V-57" stroke="#88643c" stroke-width="7"/>'
            '<rect x="50" y="-166" width="164" height="61" rx="2" fill="#e9c36c" stroke="#6d572b" stroke-width="2"/>' +
            s.text(132, -140, 'Works on', 19, 'class="display" text-anchor="middle" fill="#493c2a"') +
            s.text(132, -116, 'my machine', 19, 'class="display" text-anchor="middle" fill="#493c2a"') + '</g>')
    s.add('<g transform="translate(80 400)"><g class="pusher" data-action="launch-and-recover">'
          '<g transform="translate(0 -80)"><g class="randy-flip"><g transform="translate(0 80)"><g class="randy-facing">' +
          s.actor([(0, 0, 9)] + walking(9, 29) + [(3, 29, 35), (4, 35, 60), (5, 60, 67.5), (3, 67.5, 87)] +
                  cycle(87, 120, (6, 7), fps=3) + [(0, 120, s.end)], seamless=True) + '</g>' + sign + '</g></g></g></g></g>')
    s.visible('push-impact', 47, 54)
    s.add('<g class="push-impact motion">' + s.text(640, 258, 'oof.', 24, 'text-anchor="middle" font-weight="900" fill="' + p['red'] + '"') + '</g>')


def stack_toolbox(s):
    """Randy throws skills onto a categorized board, pauses, then repeats."""
    colors = ['#edca6a', '#8ebac5', '#a8c18d', '#bd9db9', '#e4a080', '#91b2d6', '#d5bb8d', '#8ac6b2']
    n = len(s.skills)
    sections, slots, bottom = toolbox_layout(s.skills)
    offset_y = s.height - 360
    gap = max(6.5, min(9, 52 / n))
    throws = [18 + i * gap for i in range(n)]
    board_ink = '#ece8cf' if s.dark else '#493d2d'
    board_fill = '#29443c' if s.dark else '#dfcca6'
    s.add('<g data-prop="skills-board" aria-label="Skills board organized by category">'
          f'<path d="M300 {bottom + 5}L297 {s.height - 80}H310L313 {bottom + 5}M844 {bottom + 5}L841 {s.height - 80}H854L857 {bottom + 5}" fill="#a47d50" stroke="#684d34" stroke-width="2"/>'
          f'<path d="M286 98L868 100 870 {bottom + 16} 288 {bottom + 18}Z" fill="#b28b5b" stroke="#684d34" stroke-width="3" stroke-linejoin="round"/>'
          f'<path d="M298 110L856 112 858 {bottom + 5} 300 {bottom + 6}Z" fill="{board_fill}" stroke="#8f704b" stroke-width="1.5"/>'
          f'<path d="M292 117L294 {bottom - 2}M864 117L866 {bottom - 2}" fill="none" stroke="#cda875" stroke-width="2"/>')
    for section in sections:
        x, y, width = section['x'], section['y'], section['width']
        s.add(f'<g data-board-section="{escape(section["name"], quote=True)}" data-section-x="{x}" data-section-y="{y}" data-section-width="{width}" data-section-height="{section["height"]}">' +
              s.text(x, y + 17, section['name'], 18, f'class="display" fill="{board_ink}"') +
              f'<path d="M{x} {y + 22}H{x + width}" stroke="{board_ink}" stroke-width="1" opacity=".3"/></g>')
        if width == 260 and x == 306:
            s.add(f'<path d="M576 {y + 1}V{y + section["height"] - 3}" stroke="{board_ink}" stroke-width="1" opacity=".25"/>')
    s.add(f'<g fill="#684d34"><circle cx="293" cy="106" r="2"/><circle cx="862" cy="108" r="2"/><circle cx="295" cy="{bottom + 10}" r="2"/><circle cx="864" cy="{bottom + 9}" r="2"/></g></g>')
    for i, skill in enumerate(s.skills):
        x, y, width, category_index = slots[i]
        # Tiny at Randy's raised hand, larger in flight, full size against the screen.
        dx, dy = 268 - (x + width / 2), 208 + offset_y - (y + 16)
        beat = throws[i]
        inside = f'opacity:0;transform:translate({dx:.2f}px,{dy:.2f}px) rotate(-28deg) scale(.18)'
        held = f'opacity:1;transform:translate({dx - 16:.2f}px,{dy - 32:.2f}px) rotate(-28deg) scale(.18)'
        name = f'tool-skill-{i}'
        s.animate(name, [(0, inside), (beat - 2, inside), (beat - 1.99, held), (beat - .4, held),
            (beat + .01, f'opacity:1;transform:translate({dx:.2f}px,{dy:.2f}px) rotate(-28deg) scale(.18)'),
            (beat + 1.4, f'opacity:1;transform:translate({dx * .72:.2f}px,{dy * .72 - 34:.2f}px) rotate(20deg) scale(.38)'),
            (beat + 3.2, f'opacity:1;transform:translate({dx * .28:.2f}px,{dy * .28 - 24:.2f}px) rotate(-9deg) scale(.7)'),
            (beat + 5.2, 'opacity:1;transform:none'), (s.end, 'opacity:1;transform:none')],
            'opacity:1;transform:none;transform-box:fill-box;transform-origin:center', 'cubic-bezier(.16,1,.3,1)')
        s.add(f'<g transform="translate({x} {y:.2f})"><g class="{name}" data-skill="{escape(skill["name"], quote=True)}" data-category="{escape(skill.get("category", "Stack"), quote=True)}" data-action="throw-to-screen">' +
              s.block(skill, width, 32, colors[category_index % len(colors)]) + '</g></g>')
        impact = f'tool-impact-{i}'
        s.visible(impact, beat + 5.2, beat + 6.2)
        s.add(f'<g class="{impact} motion" transform="translate({x} {y:.2f})" fill="none" stroke="{s.p["ink"]}" stroke-width="2" stroke-linecap="round">'
              f'<path d="M-5-4L-9-8M{width + 5}-4L{width + 9}-8M-5 36L-9 40M{width + 5} 36L{width + 9} 40"/></g>')
    s.animate('toolbox-lid', [(0, 'transform:rotate(0deg)'), (13, 'transform:rotate(0deg)'),
        (17, 'transform:rotate(-18deg)'), (s.end, 'transform:rotate(-18deg)')],
        'transform:rotate(-18deg);transform-origin:0px 0px', 'cubic-bezier(.22,1,.36,1)')
    s.add(f'<g transform="translate(249 {222 + offset_y})" data-prop="toolbox">'
          '<path d="M0 12L153 10 151 58 2 58Z" fill="#b97563" stroke="#4b3832" stroke-width="2.5"/>'
          '<path d="M2 48H151V58H2Z" fill="#80574d"/>'
          '<g class="toolbox-lid"><path d="M0 12L1 0 152 2 153 12Z" fill="#d39a75" stroke="#4b3832" stroke-width="2.5"/>'
          '<path d="M57 0V-11H96V1" fill="none" stroke="#4b3832" stroke-width="5"/></g>' +
          s.text(77, 39, 'MY TOOLS', 17, 'class="display" text-anchor="middle" fill="#f7edcf"') +
          '<path d="M71 10H82V21H71Z" fill="#e9c36c" stroke="#4b3832" stroke-width="1.5"/></g>')
    s.animate('tool-randy', [(0, 'transform:none'), (5, 'transform:none'),
        (13, 'transform:translate(75px,0)'), (s.end, 'transform:translate(75px,0)')])
    poses = [(0, 0, 5)] + walking(5, 13) + [(3, 13, 16)]
    windup = [(0, 'transform:rotate(0deg)')]
    for beat in throws:
        poses += [(4, beat - 2, beat), (3, beat, beat + 3), (0, beat + 3, beat + gap - 2)]
        windup += [(beat - 2, 'transform:rotate(0deg)'), (beat - .01, 'transform:rotate(-7deg)'),
                   (beat + .8, 'transform:rotate(5deg)'), (beat + 3, 'transform:rotate(0deg)')]
    finish = throws[-1] + 5.2
    poses += [(0, finish, s.end)]
    windup += [(s.end, 'transform:rotate(0deg)')]
    s.animate('throw-windup', windup, 'transform:none')
    s.add(f'<g transform="translate(125 {280 + offset_y})"><g class="tool-randy"><g class="throw-windup" data-action="wind-up-and-throw">' +
          s.actor(poses, 155, seamless=True) + '</g></g></g>')


def render(module, days, skills, dark=False, username='aziz-sridi'):
    """Return a standalone animated SVG string. No network or filesystem writes."""
    validate_days(days)
    validate_config({'username': username, 'modules': [module], 'skills': skills})
    scene = Scene(module, days, skills, dark, username)
    {'tegridy-commits': garden, 'push-access': push, 'stack-toolbox': stack_toolbox}[module](scene)
    return scene.finish()


def embed(module, prefix='./dist'):
    title = MODULES[module][0]
    alternative = MODULES[module][1]
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{prefix}/{module}-dark.svg" />\n'
            f'  <img src="{prefix}/{module}.svg" width="900" alt="{escape(alternative, quote=True)}" />\n'
            '</picture>')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, default=ROOT / 'randy.json')
    parser.add_argument('--username', help='Override username; use --refresh when changing users')
    parser.add_argument('--modules', help='Comma-separated module names; omit to use randy.json')
    parser.add_argument('--theme', choices=['both', 'light', 'dark'], default='both')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--refresh', action='store_true', help='Fetch the public GitHub contribution calendar')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    if args.username:
        config['username'] = args.username
    if args.modules is not None:
        config['modules'] = [x.strip() for x in args.modules.split(',') if x.strip()]
    validate_config(config)
    cache = ASSETS / 'contributions.json'
    if args.refresh:
        days = fetch_days(config['username'])
        snapshot = {'username': config['username'], 'source': f'https://github.com/users/{config["username"]}/contributions', 'days': days}
    else:
        snapshot = json.loads(cache.read_text(encoding='utf-8'))
        if snapshot['username'].lower() != config['username'].lower():
            parser.error('The saved calendar belongs to another user. Run with --refresh.')
        days = snapshot['days']
    validate_days(days)
    themes = [False, True] if args.theme == 'both' else [args.theme == 'dark']
    skills_by_module = {m: config.get('toolbox_skills', config['skills']) if m == 'stack-toolbox' else config['skills']
                       for m in config['modules']}
    # Render and parse every output before touching a good saved calendar or artifact.
    outputs = {f'{module}{"-dark" if dark else ""}.svg': render(module, days, skills_by_module[module], dark, config['username'])
               for module in config['modules'] for dark in themes}
    for content in outputs.values():
        ET.fromstring(content)
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        (args.output / filename).write_text(content, encoding='utf-8')
    if args.refresh:
        cache.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
    manifest = {'username': config['username'], 'duration': max(module_duration(m, skills_by_module[m]) for m in config['modules']),
                'from': days[0]['date'], 'to': days[-1]['date'], 'total': sum(d['count'] for d in days),
                'skills': config['skills'], 'modules': [
                    {'id': m, 'title': MODULES[m][0], 'description': MODULES[m][1], 'duration': module_duration(m, skills_by_module[m]),
                     'section': 'Stack' if m in STACK_MODULES else 'Contributions', 'height': module_height(m, skills_by_module[m]),
                     'skills': skills_by_module[m],
                     'loop': True,
                     'files': [f for f in outputs if f in (m + '.svg', m + '-dark.svg')]} for m in config['modules']]}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    # Snippets only reference files generated in this invocation.
    prefix = './' + args.output.name
    snippets = []
    for module in config['modules']:
        if module in STACK_MODULES and not any(m in STACK_MODULES for m in config['modules'][:config['modules'].index(module)]):
            snippets.append('## Stack')
        if args.theme == 'both':
            snippets.append(embed(module, prefix))
        else:
            filename = module + ('-dark' if args.theme == 'dark' else '') + '.svg'
            snippets.append(f'<img src="{prefix}/{filename}" width="900" alt="{MODULES[module][0]}" />')
    (args.output / 'embed.md').write_text('\n\n'.join(snippets) + '\n', encoding='utf-8')
    print(f'Generated {len(outputs)} independent SVGs for @{config["username"]}: {manifest["total"]:,} contributions through {manifest["to"]}.')
    print(f'Output: {args.output.resolve()}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(f'Error: {error}') from None
