# Invisible-Osu-Sliders
This is a script to make new .osu files out of those in the folder with the exe (or with the .py scripts) where all the sliders in all of the .osu files found are glitched into being invisible.

This program abuses the way the slider rendering engine works to essentially distort the slider into being completely invisible. Normally distortion affects the sliderball too,
but I'm abusing slider snapping to force the sliderball to appear where I want it, when I want it. No part of how this works is explained by any guide online; DM me
(JPK314#4412) on Discord if you'd like to learn more about how this works or if you'd like to contribute.

The code for accurately determining slider shapes is copied from the GitHub osu-framework and osu repositories, and translated from C# to Python in a 1-1 fashion.

Thanks to Karoo for helping me understand how slider distortion works!

If you'd like an exe instead, you can download it here: https://drive.google.com/file/d/1EWGJNUaMMMb_-Uxuozy9Ys7Z84PqZmVE/view?usp=sharing

# Known Bugs
No known bugs at this time.

# TODO:
1. The sliderball movement only appears smooth when the anchor points being snapped to are placed along a vector perpendicular to the direction of the snapping. This is
theoretically fixable but will require significant changes to the creation process, and I'm not prepared to do that right now. I'd like to have this done by the end of the summer.

2. Using HR ruins the effect. The behavior for distortion is only well understood for sliders whose bounding box is located in the first quadrant of the grid (flipped vertically, as positive y is down). Theoretically, it should be possible for a slider to remain invisible even when it is flipped vertically. However, this requires a bit of research into how the location of the bounding box can affect slider distortion, and cannot be implemented with only current knowledge. There is no timeline for this change.
