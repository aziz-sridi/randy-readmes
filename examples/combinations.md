# README example

Copy the six SVG files from `dist/` into the same folder in your profile repository, then paste the following into your README. Remove any picture block you do not need.

```html
## Contributions

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/tegridy-commits-dark.svg" />
  <img src="./dist/tegridy-commits.svg" width="900" alt="Randy draws fake contribution squares, then rain washes them away." />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/push-access-dark.svg" />
  <img src="./dist/push-access.svg" width="900" alt="Randy presses git push and scatters the contribution calendar." />
</picture>

## Stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/stack-toolbox-dark.svg" />
  <img src="./dist/stack-toolbox.svg" width="900" alt="Randy places technology skills into labeled categories on a wooden board." />
</picture>
```

Each SVG has its own loop. No shared script is required.

[Usage](../README.md#usage)
