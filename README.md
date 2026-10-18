<h1 align="center">Randy READMEs</h1>

<p align="center">
  <img src="./assets/randy.png" width="110" height="165" alt="Kid Randy Marsh" />
</p>

<p align="center">Animated SVGs for GitHub profile READMEs.</p>

<p align="center">
  <a href="#tegridy-commits">Tegridy Commits</a> ·
  <a href="#push-access">Push Access</a> ·
  <a href="#skills-board">Skills Board</a> ·
  <a href="#usage">Usage</a>
</p>

---

## Tegridy Commits

Randy draws contribution squares with a crayon, then rain washes them away.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./dist/tegridy-commits-dark.svg" />
    <img src="./dist/tegridy-commits.svg" width="900" alt="Randy draws fake contribution squares, waits out the rain, and walks back to the sign." />
  </picture>
</p>

**19-second loop** · [Light SVG](dist/tegridy-commits.svg) · [Dark SVG](dist/tegridy-commits-dark.svg) · [Copy embed](examples/tegridy-commits.md)

## Push Access

Randy presses git push and scatters the contribution calendar.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./dist/push-access-dark.svg" />
    <img src="./dist/push-access.svg" width="900" alt="Randy presses git push, flips through the air, falls, gets up, and holds a Works on my machine sign." />
  </picture>
</p>

**20-second loop** · [Light SVG](dist/push-access.svg) · [Dark SVG](dist/push-access-dark.svg) · [Copy embed](examples/push-access.md)

## Skills Board

Randy throws each technology into its category on a wooden board.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./dist/stack-toolbox-dark.svg" />
    <img src="./dist/stack-toolbox.svg" width="900" alt="Randy throws 16 technology skills into labeled categories on a wooden board, pauses, and repeats." />
  </picture>
</p>

**21-second loop** · [Light SVG](dist/stack-toolbox.svg) · [Dark SVG](dist/stack-toolbox-dark.svg) · [Copy embed](examples/stack-toolbox.md)

---

## Usage

1. Copy the light and dark SVGs you want from `dist/` into a `dist/` folder in your profile repository.
2. Paste the matching snippet from [embed.md](dist/embed.md) into your `README.md`.

Use one animation or [combine all three](examples/combinations.md). Each SVG includes its artwork and animation, so no scripts or installation are needed.

Light and dark versions follow the viewer's GitHub theme. Reduced motion displays the real contribution calendars and completed skills board.

## Automatic contribution updates

The **Update contributions** GitHub Actions workflow refreshes both contribution scenes, in light and dark, daily at 04:17 UTC. It also runs when the generator or configuration changes on `main`, and can be run from **Actions → Update contributions → Run workflow**. It reads the public calendar shown on your GitHub profile, including contributions beyond commits, and commits the regenerated files. No personal access token or installed packages are needed.

Push this repository, including `.github/`, `scripts/`, `assets/`, and `randy.json`, to GitHub. The workflow uses the repository owner's username. To display a different account, set the repository's Actions variable `CONTRIBUTIONS_USERNAME`. On a fork, enable workflows in the **Actions** tab and run the workflow once. GitHub may pause schedules in inactive public repositories; re-enable the workflow if that happens.

For your profile README to receive the updates, embed the files directly from the repository running the workflow. For example, for `aziz-sridi/randy-readmes`:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/aziz-sridi/randy-readmes/main/dist/tegridy-commits-dark.svg" />
  <img src="https://raw.githubusercontent.com/aziz-sridi/randy-readmes/main/dist/tegridy-commits.svg" width="900" alt="Randy draws contribution squares, then rain washes them away." />
</picture>
```

Replace the owner and repository with your fork's details, or use `push-access` for the other scene. GitHub's image cache can delay visible updates. Downloaded copies stay at their downloaded version. Alternatively, copy the workflow, generator, configuration, and assets into your profile repository and keep using the relative embeds above.

To refresh and verify locally with Python 3.10+:

```sh
python scripts/generate.py --refresh
python scripts/check.py
```

Use `--username YOUR_USERNAME --refresh` to generate for a different account, or edit `randy.json`. If GitHub cannot be reached or returns an invalid calendar, generation stops before replacing the saved SVGs.

[Artwork credits](CREDITS.md) · [License](LICENSE)
