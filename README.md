# Invisible-Osu-Sliders
Script to make new .osu files out of those in the folder where all the sliders are glitched into being invisible.

This program abuses the way the slider rendering engine works to essentially distort the slider into being completely invisible. Normally distortion affects the sliderball too,
but I'm abusing slider snapping to force the sliderball to appear where I want it, when I want it. No part of how this works is explained by any guide online; DM me
(JPK314#4412) on Discord if you'd like to learn more about how this works or if you'd like to contribute.

The code for accurately determining slider shapes is copied from the GitHub osu-framework and osu repositories, and translated from C# to Python in a 1-1 fashion.

Thanks to Karoo for helping me understand how slider distortion works!
