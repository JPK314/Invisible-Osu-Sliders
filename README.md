# Invisible-Osu-Sliders
This is a script to make new .osu files out of those in the folder with the exe (or with the .py scripts) where all the sliders in all of the .osu files found are glitched into being invisible.

This program abuses the way the slider rendering engine works to essentially distort the slider into being completely invisible. Normally distortion affects the sliderball too,
but I'm abusing slider snapping to force the sliderball to appear where I want it, when I want it. No part of how this works is explained by any guide online; DM me
(JPK314#4412) on Discord if you'd like to learn more about how this works or if you'd like to contribute.

The code for accurately determining slider shapes is copied from the GitHub osu-framework and osu repositories, and translated from C# to Python in a 1-1 fashion.

Thanks to Karoo for helping me understand how slider distortion works!

If you'd like an exe instead, you can download it here: https://drive.google.com/file/d/15xKmuqlz6slI-f75KtUnZmoKXuiwgtyD/view?usp=sharing

# This will be integrated into the next release of Mapping Tools. The script version in this repository is no longer supported.
