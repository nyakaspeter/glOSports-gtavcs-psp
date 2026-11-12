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
480×360 and the FPS counter, capped at 30. Standing at the barracks and in
the opening cutscene it holds the cap; on a busy street it runs at 29.5 (27–28.5 with many peds in view)
standing among ~730 draws a frame and at 29.6 on average while moving, with
two to four half seconds in twelve seconds at 27–28.5 as new streets load (see "On a busy street"; it was 24.6
standing and 27 moving with dips under 20). It is not a steady 30 there:
the heaviest views still sit a few frames under it. Most of LCS's patches
are carried over (table below), with PGO.
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
| `build.sh` | Clones vice-city-stories-recomp at `8d15d83` into `upstream/`, applies `patches/`, cross-compiles `VCSNative` in Docker (Debian trixie, GCC 14: its FFmpeg 7.1 matches the headers upstream vendors; the console's glibc is 2.44). `build/` is kept: later builds are incremental. `./build.sh <ninja target>…` builds only those. `PGO=generate|use|off` (use is the default once `pgo/` has a profile), `GEN_OPT` (generated units at `-O3` by default; upstream builds them at `-O2`), `BUILD_DIR`, `IDENTITY=0` (the guest memory window instead of identity fastmem), `LINES=1` (line tables for `tools/guest-profile.py`). |
| `package.sh` | `out/gtavcs-psp/`: the stripped binary, `lib/`, `start.sh`, `config/`, `gtavcs-psp.puppy`, `icon.png`, `glos/` (from `../goodluckOS-mali-driver/glos`). |
| `patches/` | every change to upstream, applied in order. A kept change is a new patch (`tools/mkpatch.sh NNNN-name <paths under upstream>`) and an entry below. |
| `config/` | `VCSNative.ini`. |
| `tools/` | Mac-side scripts (`vfpu-lower.py` and `vfpu-ct-test.py`: the VFPU compile-time forms of 0012 and their check); `tools/src/fbpan.c` (`build-tools.sh` builds `glos/fbpan.so`). The console-side test tools are shared: `../goodluckOS-tools/testing-sync.sh gtavcs-psp` / `testing-clean.sh gtavcs-psp`. |
| `tools/pgo.sh train` | runs the instrumented build on the console through the intro, the opening cutscene, ~60 s of walking and 90 s along a busy street, SIGUSR1, fetches its profile into `pgo/` |
| `tools/street-bench.sh`, `guest-profile.py`, `pgo-hot.py` | the street benchmark and its profiles (see "On a busy street") |
| `tools/gpr-cache-check.py`, `unit-hooks.patch`, `hooked-pcs.txt` | for regenerating the units (see Traps) |

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

From LCS 0042–0049 (checked off the device when made; on the console they
run in every build measured in "On a busy street", with the profile
retrained):

| Patch | What |
|---|---|
| 0012 | VFPU compile-time forms (LCS 0042), in the shared `allegrex_context.hpp` and the generator's lowering pass: the generic operations with literal registers (vcrsp/vqmul, vhdp, vx2i, vh2f, vf2h, vocp, vmin/vmax, vscmp/vsge/vslt) skip all prefix work while no prefix is pending (checked at run time; a pending one takes the generic form), vmmul is NEON, and the prefix-aware vtfm block, which VCS's generator emits for every vtfm (337 sites: VCS has no NEON code generation), runs as LCS 0036's NEON vtfm while no prefix is pending. 797 sites in 137 units (`tools/vfpu-lower.py`); `tools/vfpu-ct-test.py upstream/profiles/vcs/generated upstream/include`: 287,600 checks of every register combination the units use against the generic forms, bit for bit (a NaN equals any NaN). |
| 0013 | guest stores mark pages in a byte table instead of bumping page generations (a load, an add and a store each; LCS 0043), folded into the generations before the GE worker can reach new commands: at every enqueue and every stall-address update (VCS's worker runs a list while the game still writes it) |
| 0014 | `VCS_SMOOTH_CLOCK=1` (LCS 0044): the game's timer reads (sceKernelGetSystemTime/Wide/Low, pad sample times) follow real time through an offset set at each vblank wait, the scheduler, audio and vblank interrupt keep the guest clock (which snaps to vblank boundaries, so the game stepped 33 or 50 ms a frame). `VCS_FPS_CAP=<n>`: at most n game frames a second, a game frame being a vblank wait after which the game's frame counter (gp-8852) has moved, so movies and loading screens (every vblank, counter still) are not held back as by the cap removed in 0006; a frame that ran late starts the 1/n s grid again (no frames above the cap after a dip, as LCS 0047). Under GLES 2 the in-frame FPS overlay is left to the backend (0015) |
| 0015 | `VCS_GLES_MIN_PIXELS=<n>` (LCS 0045): meshes whose bounding box, wholly in front of the camera, projects to less than n pixels along both axes are not drawn (perspective views only; LCS street benchmark 26.2 → 30.0 fps at 4); `ShowFPS` drawn on the screen as the goodluckOS Android ports do it (LCS 0046): "28 fps" top left, 5×9 font at 2 pixels a dot, off-white with a dark shadow, counted over whole seconds (LCS 0048); `VCS_FPS_CAP` also paces the presents (LCS 0049: frames queued during a dip reached the screen in a burst above the cap) |

| Patch | What |
|---|---|
| 0016 | the generator: `--cache-gpr` (LCS 0035: inside a leaf or call function the guest registers live in host locals, loaded and stored where two dataflow passes place them; the hooked functions and the LZ copy loop keep theirs in the context) and `--indirect-functions` (functions no `jal` names, a jump into a function some `jal` names as a tail call instead of shared instructions, candidates that are a label inside a larger one dropped, functions that cross a unit boundary emitted with their entry's unit, functions that keep `$ra` outside their frame, routines that share instructions merged into one function with several entries, computed jumps as a switch over the function's blocks); `PSPRECOMP_SELECTION_LOG=1` lists what stays in its unit and why |
| 0017 | the units regenerated with those (10,549 functions; `tools/gpr-cache-check.py` clean) and upstream's hooks re-applied (`tools/unit-hooks.patch`, which also carries the two `VCS_GPU_CLIP` hooks in unit 0085) |
| 0018 | palette checksums over the entries the texture's index width reaches; `VCS_GPU_CLIP` (`host/vcs_world_clip.hpp`); texture signatures in NEON lanes, re-checked every fourth frame (`VCS_GLES_TEXTURE_RECHECK=1`: every frame); the GE list's stall address read when reached; the FPS log's render thread line; `VCS_GLES_UPLOAD_LOG=1`; a per-upload copy of every texture nobody read removed; the displayed target picked from a flat list instead of a hash map lookup per batch; the SAS mixer skips a silent bus and multiplies by 32-bit gains (same sums); expired thread delays looked for before a list is allocated; the texture signature cache at 4,096 slots (in 1,024 a street's textures, a signature per mip level, evicted each other and were hashed every frame: 9% of the GE worker's samples; two moving runs after: 29.7 and 29.7, minimum 27.4 and 27.3) |

| 0019 | identity fastmem (`PSPRECOMP_FASTMEM_IDENTITY`, `IDENTITY` in `build.sh`): guest memory at its own addresses, the fault handler that maps other mirrors and zero pages on demand and emulates first-page accesses, `PSPRECOMP_FASTMEM_SELFTEST`; `lwl`/`lwr` (unaligned loads, 1,684 sites) inline through the fastmem view instead of calls into the core library (a tie in two moving runs, 29.5 and 29.4; kept for the calls it removes) |

See "On a busy street" for what each did.

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

## On a busy street (2026-11-12)

The barracks numbers above say little about play: on a street the old build
ran at 22–27 and dipped under 20 while moving. `tools/street-bench.sh` measures
that without touching the console: it loads the save, writes a position on the
avenue through Little Havana into the player ped (guest `0x098B0930`; the
first write leaves the barracks' interior) and, with `SWEEP="-3 40 6 2"`,
moves the player 40 m along the avenue every 2 s (the streaming, traffic and
peds of driving; no vehicle physics). Standing there the view differs from
run to run (590 to 830 PSP draws a frame): compare runs with equal draws.
`FRAMELOG=file` keeps the game thread's time per frame (frame, wait for the
GE worker, hand-over to the render side, guest code), `DURING=dir` samples the
game thread while it measures (`tools/guest-profile.py`, on a `LINES=1` build,
names the samples by guest function), `IOCTL=1` counts the driver's kernel
calls, and the FPS log has a line for the render thread (waiting for a frame,
texture uploads, GL calls, CPU time).

What the frames were made of, old build, moving along the avenue (540 PSP
draws a frame, 36 ms a frame): 30 ms of guest code, 2 ms waiting for the GE
worker, 4 ms handing the frame over (the render side still busy with the last
one). Each stage alone sat near 30 ms, so every one of them had to get
cheaper.

| | standing, ~820 PSP draws | moving (sweep) |
|---|---|---|
| the build before (0001–0015) | 24.6 fps | 26.8–27.6, minimum 19.5–21.5, 26% of the frames over 40 ms |
| registers in locals, functions no `jal` names | | 27.6, minimum 22.2 (guest code 29.9 → 27.2 ms a frame; the render side now held the game thread back) |
| palette checksum range, GE worker | 27.0 | 28.8, minimum 24.3, 10% over 40 ms |
| the GL driver clips (stale profile; `VCS_GPU_CLIP=0` in the same binary: 25.5 at 831 draws) | 27.1 at 736 draws | |
| all of it, profile retrained on the street | 28.9 at 728 draws, minimum 25.7 | 29.1, minimum 24.8, 5% over 40 ms (guest code 25.8 ms a frame, GE worker 18.5 against 24.3) |
| the PSP's memory at its own addresses (same profile) | 28.9 at 718 draws, minimum 26.9 (the render thread now the limit: 28.9 ms of CPU a frame) | 29.8 and 29.5 in two runs, minimum 28.8 and 25.6, 4% over 40 ms (guest code 24.1 ms a frame) |
| the build as packaged, with the 30 cap of `start.sh` | 27.1 at 735 draws, minimum 25.4 (more peds in view; the game thread the limit in that run) | 29.7, minimum 27.8; without the cap 29.5, minimum 26.9, 4% over 40 ms, none over 47 (guest code 23.1 ms a frame) |
| the frame hand-over without a hash map lookup per batch (2% of the game thread), as installed | 29.7 at 716 draws, minimum 26.9, 3 of 20 half seconds under 29 (the render thread the limit: 29.0 ms of CPU a frame) | 29.6, minimum 27.3, 5% over 40 ms |
| merged entries and computed jumps as functions (retrained), the SAS mixer's gains as 32-bit products, as installed | 29.6 at 725 draws, minimum 27.6, 2 of 21 half seconds under 29; with the cap 28.5 at 759 draws | 29.3–29.7 in four runs, minimum 25.9–28.0, 3–5% over 40 ms (guest code 21.6–22.7 ms a frame) |
| the opening cutscene (`tools/cutscene-bench.sh`, 532 draws) | 29.7, the game thread 58% busy | |

The standing figures move by 2 fps between runs with the peds and cars in
view; the moving ones by 1. The cap of `start.sh` costs nothing there: two
alternating pairs standing, 29.6 and 29.7 with `VCS_FPS_CAP=30` (725 and 746
draws, 2–3 of 20 half seconds under 29) against 27.6 and 28.1 without (750
and 761 draws): the runs differ by their peds, not by the cap.

What was done, by weight:
- **Palette checksums over the entries a texture can index.** The key of a
  paletted texture includes a checksum of its palette; for a 4-bit texture
  that covered the 256 entries the mask allows (GTA leaves it at 0xFF), not
  the 16 it can read. Whatever lay behind the palette changed, the texture
  got a new key and was decoded and uploaded again: the 256×256 font page
  with its 8 levels every frame (350 KB, 2–3 ms of the render thread, a dead
  copy left in the cache each time), and whole groups of textures whenever
  streaming rewrote a neighbour's palette (250–400 KB a frame for seconds
  after each move: the dips to 22). Standing 24.7 → 27.0, moving 27.6 → 28.8
  with the minimum from 21.5 to 24.3, on the same code otherwise.
- **The GL driver clips the world** (`VCS_GPU_CLIP`, on; 0: the game clips).
  The PSP's chip drops a triangle that leaves its drawing space, so the game
  clips every mesh that crosses an edge of the view itself: a per-vertex walk
  (`0x08A09B2C`, 9% of the game thread on the street), a CPU clipper
  (`0x08A08F00`) and the pieces as separate primitives. Under GLES 2 such a
  mesh takes the game's own path for meshes wholly inside the view (the two
  places that choose are hooked in unit 0085, `host/vcs_world_clip.hpp`): 11%
  fewer PSP draws on the street (736 against 831), same picture.
- **Guest registers in host locals** (LCS 0035, `--cache-gpr`) and **more of
  the game as functions** (`--indirect-functions`): functions no `jal` names
  (virtual methods, callbacks), a jump into another function as a tail call
  instead of shared instructions, functions that cross a 16 KB unit boundary
  and ones that keep `$ra` in another register; routines that share
  instructions (a second entry point, a common tail) merged into one
  function with several entries (a `jal` to one of the others calls the
  function at that entry's id); a computed jump (a jump table, a tail call
  through a pointer) as a switch over the function's own blocks. 10,549
  functions instead of 7,029 (739,000 instructions of 958,000; what is left
  is mostly not code), 98% of the generated code's samples now in function
  form (unit bodies 0.8% of the game thread's listed samples, from 13%). Guest code per
  frame while moving: 29.9 → 27.2 ms. `tools/gpr-cache-check.py` checks the
  register traffic of every function by abstract interpretation, independently
  of the generator's dataflow (40 random single deletions: 35 caught, the
  other five dead stores).
- **The GE worker**: texture signatures hashed in four 32-bit NEON lanes and
  re-checked every fourth frame per cache slot (LCS 0019; the 64-bit hash of
  textures whose 64 KB pages were written was a tenth of the worker), and the
  stall address read only when the list reaches it instead of an atomic load
  per command (5.6% of the worker: the game thread's cache line each time).
- **The PSP's memory at its own addresses** (`IDENTITY`, on in `build.sh`).
  RAM and VRAM are mapped at their guest addresses, as the user, uncached
  and kernel mirrors of two files in `/dev/shm`, the scratchpad at
  `0x00010000`, and the executable is linked at `0x10000000`, clear of them:
  a guest address is the host address, so a guest load is one host load with
  the guest's own base register and offset (the window needed a mask and its
  base added, and a register for the base). Guest code per frame 25.8 →
  24.1 ms. What the window gave for free is kept by the fault handler: an
  access through another mirror maps that mirror, any other address gets
  zero pages, and for the first page, which cannot be mapped, the handler
  emulates the faulting load or store itself (a load reads zero, a store is
  dropped; the Thumb-2 forms GCC emits for the accessors, core, VFP and NEON
  registers). `PSPRECOMP_FASTMEM_SELFTEST=1` runs every form through it at
  start and prints the verdict; `[fastmem]` lines in the log name the first
  16 such accesses of a run (none in the benchmarks).
- The profile is trained on the street as well (`tools/pgo.sh train`).

What limits it now: the game thread (flat: no function above 2.2%; with peds
and cars around, the collision helpers at `0x088B0xxx`–`0x088B4xxx` are a
fifth of it, already compile-time VFPU forms; host code is another fifth,
the SAS mixer 3%) and the render thread, which
is CPU time in ARM's driver: about 45 µs a GL draw, 27 ms at 630 draws. A
tenth of that is the driver's search for free GPU address space
(`_mali_mmu_virtual_address_range_allocate`, a walk of its free list) for the
~140 blocks of vertex output it allocates and frees every frame (MEM_ALLOC
and MEM_FREE: 5.7 ms a frame in the kernel calls alone), which follows the
vertex count.

Tried, no gain: `VCS_GLES_UPLOAD_THREAD=1` with `VCS_GLES_TEXTURE_POOL=1`
(26.0 against 27.6 moving), `VCS_GLES_VSYNC=0` (27.7 against 27.6),
`VCS_GLES_VBO=0` (render thread 35 ms against 32), `VCS_GLES_PRETRANSFORM_MAX=0`
(a tie). In the kernel module (`goodluckOS-mali-driver`): every
MEM_FREE stalls the running GP and PP jobs' MMUs to zap their TLBs; with the
zap put off to the next mapping in the session (one for a run of frees) a
free took 14 µs instead of 20 and an allocation 16 instead of 20, 0.4 ms a
frame of the 5.7 those calls cost: the rest is the calls themselves. Not
kept (the port ships the stock module). The frame cap with slack (a frame late by
up to 17 or 34 ms keeps the 1/30 s grid, so the next comes sooner): 29.7 and
29.6 against 29.4 moving, the same; removed. The slow frames are not the
grid: in them the guest code takes 25–32 ms and the game thread then waits
7–12 ms for the render side. Without the present pacing (the cap in
the vblank wait only) the swaps ran between 16 and 60 a second (the copies
VCS draws between its frames are presented too): the pacing stays. In the backend: ARM's driver gives a draw of more than 256
vertices its own GPU memory blocks for the transformed positions and
varyings (`_gles_gb_mali_mem_alloc_position_varyings`: above 4096 bytes
each), which is where the ~140–200 allocations a frame come from; drawing
runs in pieces of at most 256 (or 192) vertices took the allocations from
5,200 a second to 900, and the 110–170 extra GL draws cost what that saved
(render thread 31.2 and 32.0 ms of CPU a frame against 29.9). Removed.
In the generator: small leaf functions emitted in place at their `jal`
(12,192 sites, the register cache carried through, checker clean, profile
retrained): guest code 25.1 ms a frame moving against 22.7, 29.2 fps against
29.6. Removed. In the memory view: word stores as typed stores and 16-bit page
marks, so that a guest store no longer makes the compiler reload the FPU and
VFPU registers it holds (a byte-wise store may alias the context's floats;
by the functions' statement mix about a quarter of the sampled generated code
is FPU and VFPU statements): guest code 22.7 ms against 22.7, 29.6 fps,
minimum 27.8, the same. Then every store that way (bytes through an
enumeration type, halfwords typed, 32-bit page marks; a measurement only,
two overlapping stores of different widths are no longer ordered for the
compiler): 22.4 ms median against 22.3–22.4. Nothing a guest store can
alias costs anything measurable, which is all that FPU and VFPU registers in
host locals would remove. Removed.
Fewer GL draws by grouping: the merge joins only draws that follow each other
with equal state. Counted per frame on the street (660 GL draws from 765 PSP
draws): 91% of the draws have alpha blending on (the game leaves it on for
the world), so their order matters unless a draw is shown to be opaque; with
that shown per draw (every vertex colour with full alpha, no texel under 255
or the texture's alpha unused: 39% of the draws), grouping the opaque draws
between two others by state would leave about 617 GL draws of 640 (3%), and
650 would become 610 if every depth-written blended draw could be moved (7%):
nearly every object has its own texture and matrix. With those draws'
vertices also transformed on the CPU, so that matrices no longer keep them
apart, 602 of 670 (10%), paid for with 36-byte instead of 10-byte vertices to
upload for them. That last form built (the opaque draws of up to 512
vertices between two others regrouped by state on the transform thread and
transformed there): 587–600 GL draws from 733–745 PSP draws instead of about
640, and the render thread at 30.2 ms of CPU a frame against 28.7, 28.9 fps
against 29.6 at that view: the draws saved cost less than the 36-byte
vertices added (197 KB a frame against 90). Removed.
The form without the transform built as well (the opaque draws regrouped by
the state the merge compares, the packed, raw and float vertex arrays laid
out again in the new order): moving only the packed and raw draws saved
nothing (what regroups are the small draws the transform thread already
transforms, which share uniforms); with those moved too, 636 GL draws from
759 PSP draws instead of about 654 (18 fewer), at 24.2 fps against 27.5–28 at
such a view, the render thread at 31.1 ms of CPU a frame and the transform
thread twice as busy. Removed.
The calls around a draw: the attribute pointers left where they are from draw
to draw (98% of the GL draws have no indices and can pass their start as
glDrawArrays' first vertex; three to eight glVertexAttribPointer calls a draw
otherwise, about 1,900 a frame): 29.2 ms of render thread CPU for 631 GL
draws, 46 µs a draw as before. The time is inside the driver's draw call.
Removed.

In the kernel module (`goodluckOS-mali-driver`, kept): a quarter of the render
thread is inside the driver's kernel calls, most of it the ~140 `MEM_ALLOC`
and `MEM_FREE` a frame for the vertex output of draws over 256 vertices. The
module now keeps a freed allocation's records for the next allocation of that
size (`mali_mem_park`, see that repo's README): an allocation 8.1 µs instead
of 14.3, a free 11.5 instead of 14.7, the render thread at 26.9–27.7 ms of
CPU a frame for 616–623 GL draws (28.7–29.2 before), 19.9 ms against
20.6–22.1 while moving. The frame rate at the busiest views is unchanged
(29.5–29.7, minimum 26.5–28.5): there the game thread itself runs 31.9 ms of
guest code a frame (the peds and traffic around the player).

The generated units at `-O2` instead of `-O3` (`GEN_OPT=2`, same profile):
5% less code (31.8 MB against 33.5), guest code 22.2, 22.5 and 21.7 ms a frame
moving against 22.3–22.7: a tie. The game thread's samples lie in 6–10 MB of
code (half of them in 615 pages), far more than the 512 KB cache and the
256-entry TLB hold, and the kernel has no huge pages. At `-Os` (25.0 MB of
code) the guest code took 25.9 ms a frame, 29.0 fps with a minimum of 23.1:
smaller is not faster here.

### Where the game thread's time goes (CPU counters)

Read with `pmuon.ko` and `pmuread` (`goodluckOS-tools/testing`), the game
thread alone on one core, standing on the busy street: 300 million
instructions a second in 1,070 million cycles (0.28 instructions a cycle).
A second holds 4.3 million L1 instruction cache refills against 1.3 million
for data, 2.0 million L2 refills (reads from RAM, 5.8 per 1,000
instructions; at 120–150 cycles each a quarter of the thread's time),
1.7 million branch mispredictions and 340,000 TLB misses (150,000 for code,
190,000 for data). A frame runs through about 4 MB of code and data with a
512 KB L2 cache: the thread waits for RAM, mostly for code. The generated
code is Thumb-2 already; smaller code by `-Os` executes more instructions
and measured slower (above), `-O2` a tie.

**Huge pages would not help.** `tlbcal` (same tools) measures a TLB miss at
18–25 cycles on this CPU with the page tables in the cache, and shows the
counters count main TLB misses (none up to 200 pages, 0.7–0.9 per access
over 400). 340,000 misses a second are then about 1% of the game thread
(3% if every table read missed the cache too); the render thread has 1.1
million a second, 2.5–3% of it, most of them in the driver's and the
kernel's own memory, which huge pages for the game would not cover. The
stock kernel has neither transparent huge pages nor hugetlbfs (32-bit ARM
has them only with LPAE, which it is built without).

The SAS mixer on a helper thread (the guest's sceSasCore call waiting for
it): 807 µs a call against 450–560 on the game thread itself. Removed.

Kernel module, second step (`mali_mem_park_lazy`, see
`goodluckOS-mali-driver`): a free 8.8 µs instead of 13.5, an allocation 7.6
instead of 8.5, about 0.8 ms a frame of the render thread; standing at
604–618 GL draws the render thread took 27.3–27.8 ms of CPU, 29.5–29.6 fps.

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
- Regenerating the units (generator built natively in the builder image:
  `g++ -O2 -std=c++20 -Iupstream/include upstream/profiles/vcs/tools/vcs_codegen_main.cpp
  upstream/src/*.cpp`): `vcs_recomp game/EBOOT.ELF --auto <dir> 0x08804000 16384
  --leaf-functions --call-functions --cache-gpr --indirect-functions
  --leaf-exclude tools/hooked-pcs.txt`, then `patch -p1 < tools/unit-hooks.patch`
  in `<dir>` (upstream's hand-made hooks and this port's two; the functions
  they edit keep their registers in the context, and one that crosses into
  the next unit stays in its unit), then `tools/gpr-cache-check.py <dir>`,
  which must report no violations. Without the two new flags the generator
  reproduces the units as 0010/0012 had them. Without the 16 KB unit size it
  makes 30 units, not upstream's 234.
- A build's time: the instrumented one about 50 minutes (`JOBS=6`), a
  profile-guided one 8, a change to host files only 2. Edit nothing under
  `upstream/` while one runs, nor a script while it is in use (the shell
  reads scripts as it goes). A host function changed after the training has
  no profile until the next one.
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

## Licence

The port's own code is MIT (`LICENSE`); `package.sh` puts a copy into the game folder's
`licenses/`. Third-party components and their licences: `licenses/README.md`.
