# Vox-Cleaner-V2
Voxel Model Cleaner & Exporter, an add-on for Blender 3.0+!

How does the cleaning procedure work: 

1. Remove all the double verts & duplicate the original model.
2. Add a new material to the Duplicate model with a generated image texture having specified properties
3. Cube project the duplicate model to generate a UV layer
4. Geometry Decimation using a decimate modifier with Planar mode
5. UV Scaling for Pixel-Perfect textures
6. Bake colors from the Original model to the duplicate model with predefined settings, as most of the voxel models dont have much different bake settings.
7. That's how your model is Much more optimized!

Besides these, there is a 2-Step Process that provides more control over the UV process. Batch Cleaning, Emission Support & Single-Click Exports are some extra features that are available as well!


Happy Cleaning! Cheers!

Farhan, The Creator of Vox Cleaner
Instagram/Twitter @TheStrokeForge
