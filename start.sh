#!/bin/sh
# GTA Vice City Stories (vice-city-stories-recomp) on goodluckOS, drawn with
# GLES 2 on ARM's Mali driver (glos-gpu). Game files (US v1.03, ULUS-10160):
# game/EBOOT.ELF (the disc's PSP_GAME/SYSDIR/EBOOT.BIN, decrypted) and
# game/PSP_GAME/. Saves in game/PSP/SAVEDATA/. Logs to /dev/shm/vcs.log.
cd "$(dirname "$0")"
# Xbox-style positions (A = bottom), as in the other GTA ports.
export SDL_GAMECONTROLLERCONFIG="1900c621474133362d4d422047616d00,GA36-MB Gamepad,a:b0,b:b1,x:b3,y:b2,back:b8,start:b9,guide:b8,leftshoulder:b4,rightshoulder:b5,lefttrigger:b6,righttrigger:b7,leftstick:b11,rightstick:b12,dpup:b13,dpdown:b14,dpleft:b15,dpright:b16,leftx:a0,lefty:a1,rightx:a2,righty:a3,platform:Linux"
export PSPRECOMP_CONFIG="$PWD/config/VCSNative.ini"
export VCS_STICK_SCALE=1.5      # GA36-MB sticks reach only ~2/3 of the declared range
export VCS_STICK_DEADZONE=0.12  # radial; the sticks rest up to 9% off centre after scaling
# The game's timer follows real time (the guest clock steps in whole vblanks:
# the game simulated 33 or 50 ms per frame while the frames took ~38).
export VCS_SMOOTH_CLOCK=1
# Meshes under 8 pixels on screen are not drawn, and game frames are capped
# at 30 so the rate stays even (movies are not held back).
export VCS_GLES_MIN_PIXELS=8
export VCS_FPS_CAP=30
# The game draws to /dev/fb0 through EGL; SDL is for the controller and audio only.
export SDL_VIDEODRIVER=dummy
# ARM's EGL pans the framebuffer inside eglSwapBuffers and sun4i-drm waits
# for the vblank there; the preload hands the pan to a helper thread.
export LD_PRELOAD=${LD_PRELOAD-$PWD/glos/fbpan.so}  # LD_PRELOAD= turns it off
exec ./glos/glos-gpu run mali ./VCSNative game/EBOOT.ELF game "$@" >/dev/shm/vcs.log 2>&1
