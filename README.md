# Randy README

Standalone SVG animations for GitHub profile READMEs. Includes two contribution scenes and a categorized skills board, with light and dark versions of each.

[Quick start](#quick-start) · [Animations](#animations) · [Configuration](#configuration) · [Daily refresh](#daily-refresh) · [Development](#development)

## Quick start

1. Choose an animation below and copy its light and dark SVGs from `dist/` into a `dist/` folder in your profile repository.
2. Paste its snippet from [dist/embed.md](dist/embed.md) into your profile `README.md`.

For example, the skills board:

```html
## Stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/stack-toolbox-dark.svg" />
  <img src="./dist/stack-toolbox.svg" width="900" alt="Randy places technology skills into labeled sections on a wooden board." />
</picture>
```

Each file embeds its own artwork, icons, font, and animation. A static README embed needs only the selected SVG files. No server, JavaScript, API key, or package installation is required.

## Animations

| Animation | Module | Loop | Preview and snippet |
| --- | --- | --- | --- |
| Tegridy Commits | `tegridy-commits` | 19 seconds | [Contribution drawing and rain](examples/tegridy-commits.md) |
| Push Access | `push-access` | 20 seconds | [Contribution calendar explosion](examples/push-access.md) |
| Skills Board | `stack-toolbox` | 21 seconds with 16 skills | [Skills grouped by category](examples/stack-toolbox.md) |

Use any animation by itself, or combine them. [Complete README example](examples/combinations.md).

<details>
<summary>Preview the collection</summary>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/tegridy-commits-dark.svg" />
  <img src="./dist/tegridy-commits.svg" width="900" alt="Randy draws contribution squares with a crayon, then rain washes them away." />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/push-access-dark.svg" />
  <img src="./dist/push-access.svg" width="900" alt="Randy presses git push, scatters the calendar, falls, and gets back up." />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/stack-toolbox-dark.svg" />
  <img src="./dist/stack-toolbox.svg" width="900" alt="Randy throws technology skills into labeled categories on a wooden board." />
</picture>

</details>

The skills board holds its completed layout briefly, then repeats. Its stage height and duration grow with the number of skills. Reduced-motion preferences show the original calendars and completed skills board. Contribution squares return to their real dates, counts, and colors after each loop.

The independent `randy-readme-website` repository provides sidebar navigation, individual playback controls, downloads, and embed copying.

## Configuration

Requires Python 3.10 or newer. The generator and checks use only the standard library.

Edit [randy.json](randy.json):

| Setting | Purpose |
| --- | --- |
| `username` | GitHub username for the contribution calendar and image footer |
| `modules` | Any selection of the three module IDs above |
| `skills` | 1–8 skills; Push Access uses the first three as its staircase |
| `toolbox_skills` | Optional independent list of 1–16 skills for the board; defaults to `skills` |

Each skill needs a short `name`, local `icon` filename without `.svg`, and six-digit hex `color`. Board skills can include a `category`; uncategorized skills use “Stack”. Categories appear in the order first listed.

```json
{
  "name": "Python",
  "icon": "python",
  "color": "#3776AB",
  "category": "AI & machine learning"
}
```

Bundled icons: `python`, `tensorflow`, `opencv`, `react`, `postgresql`, `flutter`, `git`, `dart`, `javascript`, `html5`, `css`, `firebase`, `supabase`, `mysql`, `cplusplus`, `linux`, `figma`, `postman`, and `rest-api`. Add an SVG to `assets/icons/` to use another icon.

### Generate

```sh
# Fetch the configured user's contribution calendar and render both themes
python scripts/generate.py --refresh

# Validate generated files and every module combination
python scripts/check.py

# Render only the skills board using the saved calendar
python scripts/generate.py --modules stack-toolbox

# Render contributions in dark mode to a separate folder
python scripts/generate.py --modules tegridy-commits,push-access --theme dark --output output
```

Without `--refresh`, generation uses the saved [contribution snapshot](assets/contributions.json) and works offline. After changing usernames, run with `--refresh`; a snapshot belonging to another user is rejected. Failed downloads or invalid data preserve the saved snapshot.

Defaults are both themes, the modules in `randy.json`, and output in `dist/`. The manifest and embed snippets describe the current selection. Existing SVGs from earlier selections are retained, so use a fresh output directory when you need only a subset.

## Daily refresh

Copy `scripts/`, `randy.json`, `assets/`, `dist/`, and [.github/workflows/refresh.yml](.github/workflows/refresh.yml) into your profile repository. Set your username and modules, then push to `main`.

The workflow refreshes daily and can also run manually. It uses GitHub's built-in Actions token to commit updated artwork, retaining the latest commit's author identity. The repository must allow Actions to write repository contents. No personal access token is required.

Only public activity and private-contribution counts exposed by the profile appear. If GitHub changes its calendar HTML, validation fails and the existing artwork is preserved.

## Development

```text
randy-readme/
├── .github/workflows/refresh.yml
├── assets/
│   ├── contributions.json
│   ├── fonts/
│   ├── icons/
│   ├── randy/
│   └── weather/
├── dist/                  # Self-contained SVGs, manifest, and embeds
├── examples/              # Copyable README examples
├── scripts/
│   ├── generate.py
│   └── check.py
├── randy.json
├── CREDITS.md
└── LICENSE
```

After editing the generator, run `python scripts/generate.py` and `python scripts/check.py`. The checks cover SVG integrity, contribution data, embedded assets, repeating board animations, input validation, and all seven module combinations.

To update the separate website, run `node scripts/sync-assets.mjs` from its checkout. With the two repositories side by side, the script imports this repository's generated collection and licenses.

Original code and documentation are MIT licensed. Artwork, brand marks, and fonts have separate terms. See [CREDITS.md](CREDITS.md).
