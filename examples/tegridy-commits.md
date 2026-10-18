# Tegridy Commits

Randy draws fake contribution squares with a crayon. Rain washes them away, and he walks back to the sign. The 19-second animation preserves the real contribution calendar.

Copy both SVGs into your profile repository's `dist/` folder, then paste:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/tegridy-commits-dark.svg" />
  <img src="./dist/tegridy-commits.svg" width="900" alt="Randy draws contribution squares with a crayon, then rain washes them away." />
</picture>
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../dist/tegridy-commits-dark.svg" />
  <img src="../dist/tegridy-commits.svg" width="900" alt="Randy draws contribution squares with a crayon, then rain washes them away." />
</picture>

Set your username in `randy.json`, then run `python scripts/generate.py --refresh --modules tegridy-commits`.

[Configuration and setup](../README.md#configuration)
