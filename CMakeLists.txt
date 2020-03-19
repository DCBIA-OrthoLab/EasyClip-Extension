cmake_minimum_required(VERSION 2.8.9)

project(EasyClip)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/EasyClip")
set(EXTENSION_CATEGORY "Shape Analysis")
set(EXTENSION_CONTRIBUTORS "Julia Lopinto (University of Michigan), Jean-Baptiste Vimort (University of Michigan)")
set(EXTENSION_DESCRIPTION "This Module is used to clip one or different 3D Models according to a predetermined plane. Plane can be saved to be reused for other models. After clipping, the models are closed and can be saved as new 3D Models.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/DCBIA-OrthoLab/EasyClip-Extension/master/EasyClip.png")
set(EXTENSION_SCREENSHOTURLS "http://www.slicer.org/slicerWiki/images/1/1b/EasyClipPlanePosition.png")


#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(EasyClip)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
