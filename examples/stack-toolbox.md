# Skills Board

Randy throws each technology into its labeled category on a wooden board. The finished layout holds briefly before the animation repeats. The default 16-skill selection loops every 21 seconds.

Copy `stack-toolbox.svg` and `stack-toolbox-dark.svg` from `dist/` into your profile repository's `dist/` folder, then paste:

```html
## Stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./dist/stack-toolbox-dark.svg" />
  <img src="./dist/stack-toolbox.svg" width="900" alt="Randy throws my technology skills into labeled categories on a wooden board." />
</picture>
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../dist/stack-toolbox-dark.svg" />
  <img src="../dist/stack-toolbox.svg" width="900" alt="Skills organized into AI and machine learning, frontend, backend and APIs, databases, mobile, other languages, and tools." />
</picture>

Reduced motion shows all skills in their finished positions.

[Usage](../README.md#usage)
