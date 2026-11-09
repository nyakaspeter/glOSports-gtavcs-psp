# glOSports-gtavcs-psp — GTA Vice City Stories, native, on the GA36-MB

[vice-city-stories-recomp](https://github.com/OverkillLabs3/vice-city-stories-recomp)
recompiles the PSP game's MIPS code ahead of time into C++ (no JIT) on top of
the PSPRecomp runtime, with its own renderer for the PSP's graphics chip
(Vulkan and DirectX 12 upstream, for Windows and macOS). This repo builds it
for goodluckOS on the GA36-MB (Allwinner A33, 4× Cortex-A7 at 1.2 GHz,
Mali-400 MP2 on ARM's closed driver), as a self-contained game folder. It
follows `glOSports-gtalcs-psp`: Liberty City Stories comes from the same
PSPRecomp lineage, and its GLES 2 renderer is the starting point here.

Needs the **US release, ULUS-10160 (disc v1.03)**: the code was generated
from that exact executable. Its `BOOT.BIN` is blank, so `game/EBOOT.ELF` is
the disc's `PSP_GAME/SYSDIR/EBOOT.BIN` decrypted (pspdecrypt), SHA-256
`fee2e86c7fe457ab6da463d9fdc16f156a0900adcdaa2fd260206c11907c5d65` (the value
upstream's `prepare_game.ps1` checks; the `expected_sha256` in
`vcs_ulus10160.toml` is a different, stale one), plus the disc's `PSP_GAME/`
folder.

Where it stands: runs on the GA36-MB with the 4:3 view at
480×360 and the FPS counter. Gameplay (standing at the barracks after the
opening cutscene) went from 3.5 fps to about 33 (no cap, as LCS), see
Measurements. Most of LCS's patches are carried over (table below), with PGO.
Movies play at full speed with even pacing, the loading screens and menus
fill the screen without flicker, Start+Select quits, audio plays at real
time, and with a save present the game continues from it after the credits.

## Game files

From the US v1.03 UMD (ULUS-10160), into `/home/player/ports/gtavcs-psp/game/`:

| Path | From the disc | Needed |
|---|---|---|
| `EBOOT.ELF` | `PSP_GAME/SYSDIR/EBOOT.BIN` decrypted with pspdecrypt (SHA-256 `fee2e86c7fe457ab6da463d9fdc16f156a0900adcdaa2fd260206c11907c5d65`; the disc's `BOOT.BIN` is blank) | yes |
| `PSP_GAME/USRDIR/` | the whole folder (1.2 GB: `AUDIO`, `LUA`, `RUNDATA`, `SMALLPAD.DAT`) | yes |
| `PSP_GAME/PARAM.SFO`, `ICON0.PNG`, `ICON1.PMF`, `PIC1.PNG`, `SND0.AT3` | the disc's top-level `PSP_GAME/` files | yes (`PARAM.SFO` at least: upstream's `prepare_game.ps1` checks for it) |
| `PSP_GAME/SYSDIR/` | | no: the game runs without it |

`game/PSP/SAVEDATA/` (the saves) is created by the game.

## The game folder on the console (`/home/player/ports/gtavcs-psp/`)

| | |
|---|---|
| `VCSNative` | the game (stripped, RUNPATH `$ORIGIN/lib`) |
| `lib/` | every library it needs that goodluckOS lacks (Debian trixie's FFmpeg 7.1 and its codec libraries, OpenSSL); `console-libs.txt` is the list of what the console has |
| `config/VCSNative.ini` | the port's configuration: 4:3 view at 480×360, hardware transform, `FrameRate=60` (the game's own 30 fps limiter rounds a 34 ms frame up to 50), every desktop effect off, no generated mip chains |
| `game/` | the game files |
| `game/PSP/SAVEDATA/` | the saves, as in `glOSports-gtalcs-psp` (upstream keeps them next to the executable; never touched by tooling) |
| `glos/` | the ARM driver set from `goodluckOS-mali-driver` |
| `start.sh` | sets the environment and ends with `exec ./glos/glos-gpu run mali ./VCSNative game/EBOOT.ELF game` |
| `icon.png`, `~/.local/share/applications/gtavcs-psp.puppy` | the launcher entry (the icon is a crop of the game's own `PIC1.PNG`) |

## Repo layout

| Path | What |
|---|---|
| `build.sh` | Clones vice-city-stories-recomp at `8d15d83` into `upstream/`, applies `patches/`, cross-compiles `VCSNative` in Docker (Debian trixie, GCC 14: its FFmpeg 7.1 matches the headers upstream vendors; the console's glibc is 2.44). `build/` is kept: later builds are incremental. `./build.sh <ninja target>…` builds only those. `PGO=generate|use|off` (use is the default once `pgo/` has a profile), `GEN_OPT` (generated units at `-O3` by default; upstream builds them at `-O2`), `BUILD_DIR`. |
| `package.sh` | `out/gtavcs-psp/`: the stripped binary, `lib/`, `start.sh`, `config/`, `gtavcs-psp.puppy`, `icon.png`, `glos/` (from `../goodluckOS-mali-driver/glos`). |
| `patches/` | every change to upstream, applied in order. A kept change is a new patch (`tools/mkpatch.sh NNNN-name <paths under upstream>`) and an entry below. |
| `config/` | `VCSNative.ini`. |
| `tools/` | Mac-side scripts (`vfpu-lower.py` and `vfpu-ct-test.py`: the VFPU compile-time forms of 0012 and their check); `tools/src/fbpan.c` (`build-tools.sh` builds `glos/fbpan.so`). The console-side test tools are shared: `../goodluckOS-tools/testing-sync.sh gtavcs-psp` / `testing-clean.sh gtavcs-psp`. |
| `tools/pgo.sh train` | runs the instrumented build on the console through the intro, the opening cutscene and ~60 s of walking, SIGUSR1, fetches its profile into `pgo/` |

## Build, package, deploy

```sh
./build.sh && ./package.sh
```
A first install copies all of `out/gtavcs-psp/` to `/home/player/ports/gtavcs-psp/`, the
launcher entry to `/home/player/.local/share/applications/`, then the game
files to `gtavcs-psp/game/`. Later: `python3 ../goodluckOS-tools/mtp_send.py / out/gtavcs-psp/VCSNative`,
then over the console `mv /home/player/VCSNative /home/player/ports/gtavcs-psp/`
(MTP never overwrites, hence send-then-move).

## Patches

| Patch | What |
|---|---|
| 0001 | build: `PSPRECOMP_VCS_GE_BACKEND=GLES2` on Linux (EGL, GLES 2, SDL2, threads), with `platform/linux/` |
| 0002 | the GLES 2 GE backend, from `glOSports-gtalcs-psp` (its 0005, plus the backend parts of its 0009 strips kept as strips, 0010 off-screen draws dropped, 0018 NEON cull scan, 0025 raw vertex path (hardware-transform layouts go to the GPU as the PSP stores them; the vertex shader decodes, skins with up to 8 bones, lights with the PSP's model and generates UVs, from a 64-vec4 uniform block per state change), 0026 the merge loop on the transform thread (keys instead of GL objects, `glDrawArrays` for sequential groups), 0031 merged strips as sequential runs and constant attributes once per frame, 0037 shader variants warmed before the first frame (texture pool and upload thread opt-in, off), 0038 the driver's program binaries cached in `config/shader-cache/`) on VCS's backend interface (`ge_gpu_backend.hpp`: the raw layout and uniform block, no-zero-fill index buffers). VCS's pre-transform pass on the transform thread skips raw batches (their first vertex is a byte offset). The texture key is two 32-bit lanes, and a prim whose texture fields equal the previous one's reuses its key (~1,000 keys a frame in a cutscene). The frame shown is the target with the most geometry (sticky until another has 1.5×), as VCS's Vulkan backend does: VCS draws scene and HUD into a working buffer (0x88000) and copies it into the displayed one on the next vblank, and a vblank that draws only that small copy is not shown (it alternated with the scene: a jumping flicker). The backend presents directly only while the GE draws (movies and loading screens, which the game writes to memory, come through `present_rgba`). A target's size is the largest clip rectangle drawn into it that frame, at least 480×272: VCS composes gameplay into 512×320 and shows all of it, but lays out menus and loading screens in 480×272 and squeezes the loading art from its 512×320 working buffer into a 480×272 one (a size kept across frames showed those with black bands, and the two buffers the pause menu alternates between at two scales: flicker; a size per draw zoomed the frame whenever the help box showed). A target read as a texture is addressed by its own logical size (the loading-screen copy reads the 512×320 buffer as a 512×512 texture, and the logo was left out); only direct-colour textures count as a target read back (a palette texture loaded where a target used to be, the weapon icon after loading a save, showed a miniature of the screen). Clear-mode draws write only the channels the clear selects (colour, alpha, depth), as on the PSP: a depth-only clear painted its vertex colour, the green flash when skipping the credits. 4:3 HUD factor. `VCS_GLES_VSYNC=0` swaps without waiting for the blank; `VCS_GLES_TARGET_LOG=1` logs each vblank's targets and vertex counts. |
| 0003 | `platform/linux/display_window_sdl.cpp`: no window; SDL game controller with a radial dead zone (`VCS_STICK_SCALE`, `VCS_STICK_DEADZONE`, as LCS); frames the GE didn't draw go to the backend, converted by rows straight from guest memory and only when they changed (the generic decoder took 8.5 ms a vblank, every vblank, during movies); SIGTERM (Start+Select: `appctl stop-application`), which SDL turns into a quit event, ends the game. SDL audio (upstream's macOS audio) on Linux. |
| 0004 | 32-bit ARM: `vfmaq_n_f32` (AArch64 only) as `vmlaq_n_f32` in the renderer's NEON transforms. |
| 0005 | no CPU rasterizer under GLES 2 (the backend draws every target and serves framebuffer feedback from its GPU copy; upstream only skipped the displayed buffer, so the whole scene in the working buffer was rasterized on the CPU as well); hardware transform allowed for GLES 2 (upstream keeps it off for its Vulkan backend); the HUD and its clip rectangle squeezed vertically for a view narrower than 16:9 (as LCS 0008; the clip keeps the radar map inside its circle), towards the top or bottom by the centre of what the clip lets through (radar tiles are rotated quads far larger than the radar; by their whole extent some were squeezed towards the top, a strip of the map above the circle at some camera angles); palette checksums cached while the palette's pages are unwritten (LCS 0011/0024; VCS already hashed words as LCS 0012), and texture signatures the same way (1,024 entries); the raw vertex path (LCS 0025, `PSPRECOMP_GE_GPU_RAW`, on): a hardware-transform draw with a layout the shader decodes sends the PSP's vertex bytes and a uniform block (matrices, bones, lights, material, UV generation), sent again only when the block changes; alpha and fog control worked out once per draw instead of per vertex; the cloud camera observer (for VCS's Vulkan sky) compiled out under GLES 2 |
| 0006 | async GE (upstream's display-list worker thread, `PSPRECOMP_GE_ASYNC`) on by default under GLES 2; the audio poll without a 64-bit division (LCS 0028); audio threads catch up after the limiter moves the guest clock past a slow frame (a buffer due in the past is submitted at once instead of restarting the schedule, and the schedules no longer move with the jump: at 30 fps half the audio was never made, choppy and drifting behind the picture); the savedata utility keeps the saves in `game/PSP/SAVEDATA`, where the game's own file calls see them as `ms0:PSP/SAVEDATA` (at boot the game lists that folder with `sceIoDopen` and loads the save it finds; with the saves next to the executable it found nothing and always started a new game); only movie frames come from guest memory (a loading screen draws every 5+ vblanks, and in between the guest's own 480×272 copy replaced it); movies decode on two FFmpeg frame threads; the keyboard/controller prompt table is searched for in guest RAM only after the game has read the text file (searching all 24 MB took 95 ms and ran every 2 s until found: the intro movies stalled every 2 s); one log line per save or load (`[savedata]`); `VCS_BENCH_NEW_GAME=1` hides the saves from the boot listing, so a bench always gets the opening cutscene; file reads written straight into guest memory mark their pages as written (the palette and signature caches watch page generations). The `VCS_FPS_CAP` that was here waited 1/30 s on every vblank wait, not every frame: movies, which wait each vblank, and the guest clock with them ran at half speed, and audio starved. |
| 0007 | LCS's runtime patches, unchanged (the PSPRecomp runtime is the same in both games): 0006 guest-memory loads and stores inline, 0021 32-bit chain countdown, 0022 fastmem window with page generations, and the runtime parts of 0030 (call protocol), 0033/0034 (leaf and call functions) and 0036 (VFPU helpers) |
| 0008 | `SIGUSR1` writes the PGO profile (LCS 0007) |
| 0009 | the generator (`profiles/vcs/tools/vcs_codegen_main.cpp`): a `jal` to an import stub emitted its return and then looped without advancing (the generator grew without bound: killed at 11 GB in Docker, 79 GB natively); LCS 0020 (VFPU prefixes folded, ARM `mul.s`), 0030 (call protocol, no exceptions in the units), 0033/0034 (guest functions as host functions: leaves, then functions that call); fixed edges into addresses no unit covers go through the dispatcher; every block upstream registers stays re-enterable (the dispatcher enters inner blocks, e.g. at `0x08A070D0`), so such functions get it as a continuation |
| 0010 | the units regenerated with `--leaf-functions --call-functions` (1,559 leaves, 5,470 call functions, 55% of the code) and upstream's hand-made hooks re-applied (the 4:3 projection in units 0076/0092, camera and aim, the pool-allocator assertion in 0096) |
| 0011 | `sceKernelExitDeleteThread` deletes the thread and frees its stack (it only marked it completed: VCS ends its "sfx bank load thread", one per sound bank loaded, that way, so every building, mission, save and load leaked a stack until `sceKernelCreateThread` ran out of room and the game waited forever on a black or "Loading..." screen for the thread it could not create; how soon depended on how much had been loaded since launch). ATRAC3+ decoding on a worker thread (LCS 0029's ATRAC half): the worker owns the decoders and keeps three decoded frames per context ahead; `sceAtracDecodeData` takes the next one, and when the ring is empty (right after a decoder opens or loops) the guest thread is parked in the scheduler until the worker has it (`VCS_ATRAC_WORKER=0` decodes on the game thread). Audio blocks reach the host mixer as one copy of guest memory instead of a 16-bit load per sample. `kill -USR2 $(pidof VCSNative)` logs every guest thread, the event flags, the UMD hand-offs and the ATRAC rings at the next vblank (for a game that stops progressing without crashing). |

LCS patches not carried over: 0013–0015, 0019, 0023, 0032 (display-list
reading and prescan: VCS reads lists through its own window, "Stage 41", and
has no prescan); 0017 and 0024 (GE-thread per-draw work: the backend mutex
stays, VCS finishes frames on the game thread while the GE worker records;
the rest is VCS-structured and the GE worker is no longer the limit);
0035/0036 generator parts (guest registers in host locals, NEON VFPU: VCS's
generator emits hand-made blocks that read and write `ctx.gpr` directly,
which a register cache would have to know about; LCS measured both within
noise); 0029's SAS half (VCS mixes only through `__sceSasCoreWithMix`, into a
ring of 12 grains at 0x08C3ECC0 that the game reads back itself and copies into
the buffers it hands to `sceAudioOutput` (0x0974AE30/0x0974CE30, channel 6):
a mix still running behind the game thread would be read half done).

Built and checked off the device, not yet run on it (needs a PGO
retrain, then the gameplay and cutscene A/Bs), from LCS 0042/0043:

| Patch | What |
|---|---|
| 0012 | VFPU compile-time forms (LCS 0042), in the shared `allegrex_context.hpp` and the generator's lowering pass: the generic operations with literal registers (vcrsp/vqmul, vhdp, vx2i, vh2f, vf2h, vocp, vmin/vmax, vscmp/vsge/vslt) skip all prefix work while no prefix is pending (checked at run time; a pending one takes the generic form), vmmul is NEON, and the prefix-aware vtfm block, which VCS's generator emits for every vtfm (337 sites: VCS has no NEON code generation), runs as LCS 0036's NEON vtfm while no prefix is pending. 797 sites in 137 units (`tools/vfpu-lower.py`); `tools/vfpu-ct-test.py upstream/profiles/vcs/generated upstream/include`: 287,600 checks of every register combination the units use against the generic forms, bit for bit (a NaN equals any NaN). |
| 0013 | guest stores mark pages in a byte table instead of bumping page generations (a load, an add and a store each; LCS 0043), folded into the generations before the GE worker can reach new commands: at every enqueue and every stall-address update (VCS's worker runs a list while the game still writes it) |
| 0014 | `VCS_SMOOTH_CLOCK=1` (LCS 0044): the game's timer reads (sceKernelGetSystemTime/Wide/Low, pad sample times) follow real time through an offset set at each vblank wait, the scheduler, audio and vblank interrupt keep the guest clock (which snaps to vblank boundaries, so the game stepped 33 or 50 ms a frame). `VCS_FPS_CAP=<n>`: at most n game frames a second, a game frame being a vblank wait after which the game's frame counter (gp-8852) has moved, so movies and loading screens (every vblank, counter still) are not held back as by the cap removed in 0006; a frame that ran late starts the 1/n s grid again (no frames above the cap after a dip, as LCS 0047). Under GLES 2 the in-frame FPS overlay is left to the backend (0015). Built, not run: the VCS recomp is not on the console |
| 0015 | `VCS_GLES_MIN_PIXELS=<n>` (LCS 0045): meshes whose bounding box, wholly in front of the camera, projects to less than n pixels along both axes are not drawn (perspective views only; LCS street benchmark 26.2 → 30.0 fps at 4); `ShowFPS` drawn on the screen as the goodluckOS Android ports do it (LCS 0046): "28 fps" top left, 5×9 font at 2 pixels a dot, off-white with a dark shadow, counted over whole seconds (LCS 0048); `VCS_FPS_CAP` also paces the presents (LCS 0049: frames queued during a dip reached the screen in a burst above the cap). Built, not run |

LCS's disc reads on a worker thread are not carried over: in LCS they
measured no faster and a run with them froze, so LCS dropped them.

## Measurements

FPS log averaged over 10 s. Until async GE: the opening cutscene (first 3D
frames, ~900 PSP draws). From then on: gameplay standing at the barracks once
the HUD shows (fbprobe on the money counter), ~265 PSP draws a frame.

| | fps | |
|---|---|---|
| first run (0001–0004) | 3.5 | cutscene; game thread 99%: the CPU rasterizer ran for every target but the displayed one |
| CPU rasterizer off | 2.7–4 | GE 238 ms a frame: vertex decode 126 ms, triangle setup 65 ms (CPU transform of every vertex) |
| hardware transform on | 9.5 | game thread 72%, render thread 25% |
| 4:3 at 480×360, cap in the vblank wait, LCS runtime patches | 10.8 | GE 46 ms of a ~90 ms game-thread frame |
| async GE on vs off (same binary) | 21.3 / 23.3 vs 15.2 | game thread 93%, GE worker 54% |
| `fbpan.so` on vs off (same binary) | 20.1 / 21.3 vs 21.2 / 19.4 | tie (game-thread bound); kept for its mechanism, measured in LCS (the pan's vblank wait) |
| `-O3` units, strips, culling, palette cache (vs the previous build) | 25.0 vs 24.1 / 24.5 | scenes varied before the HUD-locked bench |
| regenerated units: leaf and call functions, call protocol, VFPU fold (vs the previous build) | 27.1 / 30.1 vs 22.3 / 24.1 | the second run at the 30 fps cap; uncapped 31.7, game thread 100% spread over the guest code |
| uncapped from here (`VCS_FPS_CAP=0`): VSync off vs on (same binary) | 27.0 vs 32.4 / 32.0 | dead end: VSync stays on |
| PGO (trained by `tools/pgo.sh`) vs without | 33.4 / 33.7 vs 28.5 / 32.9 | kept; the profile is in `pgo/` |
| shader binary cache (two launches) | 33.2, 33.3 | first launch saved 21 programs, the second loaded all 21 in 8 ms before the first frame |
| intro credits movie, `VCS_FPS_CAP=30` vs none | movie audio fed 44k vs 88k frames per 2 s | the cap halved the guest clock in movies |
| movie, FFmpeg frame threads vs none (FPS lines, 60 s) | dips only every 4th line (to ~50) vs extra dips to 43–48 | kept |
| movie, present only changed frames, rows from guest memory | present 4.4 ms a vblank vs 8.5 | kept |
| opening cutscene, main audio channel (ch8): fed per 2 s of playback, before vs after the catch-up | ~30–50k vs 88.6k of 88.6k frames, underruns climbing vs flat | gameplay too (88.6k, flat); gameplay 35 fps, unchanged |
| opening cutscene from here (`tools/cutscene-bench.sh`, ~550 PSP draws): raw vertex path (LCS 0025) vs without | 30.6 / 32.2 vs 20.4 / 21.6 | render thread no longer decodes and skins on the CPU; game thread now 93–96% |
| merge loop on the transform thread (LCS 0026) vs 0025 only | 30.8 / 31.3 vs 31.4 / 31.1 | tie, kept: render thread 87% → 72%, transform thread 13–16% |
| strip runs and constant attributes (LCS 0031) vs 0026 | 32.4 / 31.4 vs 30.8 / 30.9 | kept: 241 `glDrawArrays` and 34 indexed draws a frame, 5 KB of indices |
| gameplay at the barracks, 0025 + 0026 + 0031 vs before them | 29.5 / 29.7 vs 26.4 / 26.6 | logged PSP draws a frame 396 vs 343 (the 33 fps rows had ~265 at the same spot); game thread 91% vs 78%. The shader cache now holds 48 programs (the raw variants) |
| opening cutscene, ATRAC on a worker (0011) vs without | 33.2 / 32.9 vs 30.7 / 31.6 | kept; the worker 5% of a core |
| profile retrained on this build (`tools/pgo.sh train`, now on a new game: with a save the game skips the cutscene) vs the old profile | cutscene 32.3 / 33.7 vs 33.0 / 32.6; gameplay 30.0 / 30.0 vs 29.5 / 29.8 | kept: render thread 56–57% vs 61–62% in gameplay |
| movie, prompt-table search only after the text file is read | 900 vblanks: average 16.68 ms, none over 25 ms, vs one 100 ms vblank every 120 | the stall was the RAM search in the vblank wait (`sceDisplayWaitVblankStart` timed at 94 ms) |

## Traps

- `appctl stop-application` returns before the game has exited; a launch sent
  within a few seconds is killed by the late shutdown. Wait until
  `pidof VCSNative` is empty. On 2026-10-31 appd also ended up with two
  daemons and two launchers after a shutdown, and launch requests were no
  longer acted on (nothing outside the game folder was changed).
- `/home/player` is FAT: unpack with `tar -xof` (no owners).
- After the credits movie (A skips it) the game loads the save in
  `game/PSP/SAVEDATA/` if there is one, else starts a new game; other saves load
  from the pause menu (Game, Load Game). Injected presses (padpress) must be held ~600 ms: the game
  reads the pad once per frame.
- appd: the first launch after the launcher has started is often killed by
  an appd restart 0.2 s later; the bench retries the launch. A retry sent
  while the first launch is still loading the driver kills both, and can
  leave the display without `/dev/fb0`: `glos/glos-gpu-switch lima`, then
  `glos_fbfix.ko` with `overalloc=100` and `recreate=1`, unloaded again,
  brings it back. Check for `VCSNative` with `ps`, not `pidof`, after ~20 s.
- Regenerating the units (generator built in Docker, run with a memory cap):
  `vcs_recomp game/EBOOT.ELF --auto <dir> 0x08804000 16384 --leaf-functions
  --call-functions`, then upstream's hand-made hooks (a patch from the
  regenerated to the committed units, plus the hunks that need placing by
  hand: the aspect helpers at the top of units 0076/0092, the 16:9 constant
  at 0x08937EB0, the assertion in 0096). Without the 16 KB unit size the
  generator makes 30 units, not upstream's 234.
- Profiles (`psample`) report `VCSNative+<offset>`: the packaged binary went
  through `patchelf`, so the address for `addr2line` on
  `build/bin/Release/VCSNative` is offset + 0xE000. A thread blocked in a
  syscall shows `libc+0x6ad80`: those samples are waiting, not work.
- Saving at a save icon shows a black frame where the PSP draws its system
  save dialog: the savedata utility completes at once, with no dialog
  (`[savedata] mode=5` in the log).
- A hang on a loading transition (save, load, mission, interior) with the
  stream thread idle: first look at the thread list (`kill -USR2`). Dead
  threads piling up was the leak 0011 fixes; the UMD hand-off race upstream
  guards against (`io_handoff_release_pc`) looked like the same symptom but
  was not it.
- Serial line: a bench killed on the Mac keeps running in the console's
  shell; send Ctrl-C over the serial port before the next command.
