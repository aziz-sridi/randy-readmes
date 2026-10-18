# Sprite sheet generation

Built-in ImageGen, using `Deaged-Randy.png` as the reference and requesting a transparent background. The original generated PNG is preserved as `poses.png`.

```text
Use case: illustration-story / animation sprite sheet.
Asset type: one production sprite atlas for 2D paper-cutout README animations.
Input image: Deaged-Randy.png is the identity and style reference. Preserve this exact recognizable kid Randy Marsh: huge round head, black shaggy hair, enormous white eyes, small dark moustache, chin lines, teal short-sleeve shirt with two pockets and colored pencils, small dark pants, tiny body. He is a CHILD VERSION with an adult moustache. Do not age up, change costume, or replace with Stan.
Create ONE sprite atlas on a truly TRANSPARENT background. Landscape 1536x1024, exact 3 columns by 2 rows of equal 512x512 cells. No gutters, no borders, no text, no labels, no shadow, no environment, no props. One complete character centered in each cell; feet on local y=474 and head at local y=30, keep the same head size and body proportions in all six poses. Leave transparent padding around all limbs. No limbs crossing cell borders.
Cell positions left to right:
Top row: (1) front-facing neutral, hands down, deadpan. (2) facing mostly front but walking right, left foot forward, arms slightly swinging. (3) the opposite walking step, right foot forward, arms slightly swinging.
Bottom row: (4) mostly front-facing, right arm stretched horizontally to the viewer's right at chest height as if pushing a button, left hand down, determined expression. (5) front-facing startled, both arms raised beside the head and mouth a small open oval, wide eyes. (6) front-facing guilty, both hands hidden behind his back, pupils glancing to his left, closed mouth.
Match the flat handmade South Park construction-paper artwork of the reference. Subtle paper grain is okay. Crisp silhouettes and simple flat fills. Uniform character height and alignment. True alpha transparency everywhere outside the six characters. This is one sprite-sheet asset, not a comic or scene.
```
