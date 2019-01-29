# Blender Color Matching Addon

All the controls for this addon can be found in the UV editor window.

# Calculate Picture
This simply takes the maximum and minimum RGB values.  It's a good start, but keep in mind that heavily saturated colors can throw off the calculation.  For example, if the image's black's are RGB(0.1, 0.1, 0.1), but there's a heavily saturated red pixel with an RGB(0.99, 0.01, 0.01), your min color will be RGB (0.1, 0.01, 0.01), which technically isn't the black value.  That's where the color picker comes in.

# Min/Max Color Picker
You use this just like a Blender color picker: left click to color pick, right click apply and finish, or "Escape" to cancel.

This is useful for when you need a black or white value of a certain area.  Some areas of an image have different color ranges than other parts.  So the color picker is helpful to isolate these areas.

Note: the color values in the panel will reset while you color pick so it can apply the values you're currently picking.

# Reset
This resets your color values to absolute black, white, and midtone.

# Add to Compositor
Adds a color balance node to your compositor, applying the black and white values you just calculated or picked!
