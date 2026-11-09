# Third-party components

The port builds on and ships with:

| Component | Licence | Text |
|---|---|---|
| [vice-city-stories-recomp](https://github.com/OverkillLabs3/vice-city-stories-recomp) at `8d15d83`: the recompiler, runtime and host code `VCSNative` is built from | MIT | `psprecomp.LICENSE.txt` |
| ARM's Mali user-space driver (`glos/lib/libMali.so`) | ARM proprietary | `libMali.txt` |
| ARM's Mali kernel driver (`glos/mali.ko`) | GPL-2.0 | goodluckOS-mali-driver |

`VCSNative` also holds code recompiled from the game's own executable, which is Rockstar's and
not covered by any licence here.

The libraries in `lib/` are Debian trixie's armhf packages, unchanged (stripped). Each package's
Debian copyright file is here as `<package>.copyright.txt`; the licence column is the main one it
declares (the files list every licence that applies, and refer to Debian's
`/usr/share/common-licenses/` for the full GPL/LGPL texts).

| Debian package | Libraries | Licence | Text |
|---|---|---|---|
| `libaom3` 3.12.1-1+deb13u1 | `libaom.so.3` | BSD-2-clause | `libaom3.copyright.txt` |
| `libavcodec61` 7:7.1.5-0+deb13u1 | `libavcodec.so.61` | LGPL-2.1+ | `libavcodec61.copyright.txt` |
| `libavformat61` 7:7.1.5-0+deb13u1 | `libavformat.so.61` | LGPL-2.1+ | `libavformat61.copyright.txt` |
| `libavutil59` 7:7.1.5-0+deb13u1 | `libavutil.so.59` | LGPL-2.1+ | `libavutil59.copyright.txt` |
| `libbluray2` 1:1.3.4-1+b2 | `libbluray.so.2` | LGPL-2.1+ | `libbluray2.copyright.txt` |
| `libbsd0` 0.12.2-2 | `libbsd.so.0` | BSD-3-clause | `libbsd0.copyright.txt` |
| `libbz2-1.0` 1.0.8-6 | `libbz2.so.1.0` | BSD-variant | `libbz2-1.0.copyright.txt` |
| `libcairo-gobject2` 1.18.4-1+b1 | `libcairo-gobject.so.2` | see the file | `libcairo-gobject2.copyright.txt` |
| `libcairo2` 1.18.4-1+b1 | `libcairo.so.2` | see the file | `libcairo2.copyright.txt` |
| `libchromaprint1` 1.5.1-7 | `libchromaprint.so.1` | Expat | `libchromaprint1.copyright.txt` |
| `libcjson1` 1.7.18-3.1+deb13u1 | `libcjson.so.1` | MIT | `libcjson1.copyright.txt` |
| `libcodec2-1.2` 1.2.0-3 | `libcodec2.so.1.2` | LGPL-2.1 | `libcodec2-1.2.copyright.txt` |
| `libcom-err2` 1.47.2-3+b12 | `libcom_err.so.2` | GPL-2 | `libcom-err2.copyright.txt` |
| `libdatrie1` 0.2.13-3+b1 | `libdatrie.so.1` | LGPL-2.1+ | `libdatrie1.copyright.txt` |
| `libdav1d7` 1.5.1-1 | `libdav1d.so.7` | BSD-2-clause | `libdav1d7.copyright.txt` |
| `libdvdnav4` 6.1.1-3+b1 | `libdvdnav.so.4` | GPL-2+ | `libdvdnav4.copyright.txt` |
| `libdvdread8t64` 6.1.3-2 | `libdvdread.so.8` | GPL-2+ | `libdvdread8t64.copyright.txt` |
| `libfontconfig1` 2.15.0-2.3 | `libfontconfig.so.1` | see the file | `libfontconfig1.copyright.txt` |
| `libfribidi0` 1.0.16-1 | `libfribidi.so.0` | LGPL-2.1+ | `libfribidi0.copyright.txt` |
| `libgdk-pixbuf-2.0-0` 2.42.12+dfsg-4+deb13u1 | `libgdk_pixbuf-2.0.so.0` | LGPL-2+ and LGPL-2.1+ and CC0-1.0 | `libgdk-pixbuf-2.0-0.copyright.txt` |
| `libgme0` 0.6.3-7+b2 | `libgme.so.0` | LGPL-2.1+ | `libgme0.copyright.txt` |
| `libgmp10` 2:6.3.0+dfsg-3 | `libgmp.so.10` | GPL-2+ or LGPL-3+ | `libgmp10.copyright.txt` |
| `libgnutls30t64` 3.8.9-3+deb13u4 | `libgnutls.so.30` | see the file | `libgnutls30t64.copyright.txt` |
| `libgraphite2-3` 1.3.14-2+deb13u1 | `libgraphite2.so.3` | LGPL-2.1+ or MPL-1.1 or GPL-2+ | `libgraphite2-3.copyright.txt` |
| `libgsm1` 1.0.22-1+b2 | `libgsm.so.1` | TU-Berlin-2.0 | `libgsm1.copyright.txt` |
| `libgssapi-krb5-2` 1.21.3-5+deb13u1 | `libgssapi_krb5.so.2` | see the file | `libgssapi-krb5-2.copyright.txt` |
| `libharfbuzz0b` 10.2.0-1+deb13u1 | `libharfbuzz.so.0` | MIT | `libharfbuzz0b.copyright.txt` |
| `libhogweed6t64` 3.10.1-1 | `libhogweed.so.6` | LGPL-3+ or GPL-2+ | `libhogweed6t64.copyright.txt` |
| `libidn2-0` 2.3.8-2 | `libidn2.so.0` | GPL-3+ | `libidn2-0.copyright.txt` |
| `libjpeg62-turbo` 1:2.1.5-4 | `libjpeg.so.62` | BSD-BY-LC-NE | `libjpeg62-turbo.copyright.txt` |
| `libjxl0.11` 0.11.2-0.1~deb13u3 | `libjxl.so.0.11`, `libjxl_cms.so.0.11`, `libjxl_threads.so.0.11` | BSD-3-clause-Google | `libjxl0.11.copyright.txt` |
| `libk5crypto3` 1.21.3-5+deb13u1 | `libk5crypto.so.3` | see the file | `libk5crypto3.copyright.txt` |
| `libkeyutils1` 1.6.3-6 | `libkeyutils.so.1` | GPL-2+ | `libkeyutils1.copyright.txt` |
| `libkrb5-3` 1.21.3-5+deb13u1 | `libkrb5.so.3` | see the file | `libkrb5-3.copyright.txt` |
| `libkrb5support0` 1.21.3-5+deb13u1 | `libkrb5support.so.0` | see the file | `libkrb5support0.copyright.txt` |
| `liblcms2-2` 2.16-2+deb13u2 | `liblcms2.so.2` | MIT | `liblcms2-2.copyright.txt` |
| `liblzma5` 5.8.1-1+deb13u2 | `liblzma.so.5` | 0BSD | `liblzma5.copyright.txt` |
| `libmbedcrypto16` 3.6.6-0.1~deb13u1 | `libmbedcrypto.so.16` | Apache-2.0 or GPL-2+ | `libmbedcrypto16.copyright.txt` |
| `libmd0` 1.1.0-2+b1 | `libmd.so.0` | BSD-3-clause | `libmd0.copyright.txt` |
| `libmp3lame0` 3.100-6+b3 | `libmp3lame.so.0` | LGPL-2+ | `libmp3lame0.copyright.txt` |
| `libmpg123-0t64` 1.32.10-1+deb13u1 | `libmpg123.so.0` | LGPL-2.1 | `libmpg123-0t64.copyright.txt` |
| `libnettle8t64` 3.10.1-1 | `libnettle.so.8` | LGPL-3+ or GPL-2+ | `libnettle8t64.copyright.txt` |
| `libnorm1t64` 1.5.9+dfsg-3.1+b2 | `libnorm.so.1` | NRL-2-clause | `libnorm1t64.copyright.txt` |
| `libogg0` 1.3.5-3+b2 | `libogg.so.0` | BSD-3-clause | `libogg0.copyright.txt` |
| `libopenjp2-7` 2.5.3-2.1~deb13u2 | `libopenjp2.so.7` | BSD-2 | `libopenjp2-7.copyright.txt` |
| `libopenmpt0t64` 0.7.13-1+b1 | `libopenmpt.so.0` | BSD-3-clause | `libopenmpt0t64.copyright.txt` |
| `libopus0` 1.5.2-2 | `libopus.so.0` | BSD-3-clause | `libopus0.copyright.txt` |
| `libp11-kit0` 0.25.5-3 | `libp11-kit.so.0` | BSD-3-clause | `libp11-kit0.copyright.txt` |
| `libpango-1.0-0` 1.56.3-1 | `libpango-1.0.so.0` | LGPL-2+ and LGPL-2.1+ | `libpango-1.0-0.copyright.txt` |
| `libpangocairo-1.0-0` 1.56.3-1 | `libpangocairo-1.0.so.0` | LGPL-2+ and LGPL-2.1+ | `libpangocairo-1.0-0.copyright.txt` |
| `libpangoft2-1.0-0` 1.56.3-1 | `libpangoft2-1.0.so.0` | LGPL-2+ and LGPL-2.1+ | `libpangoft2-1.0-0.copyright.txt` |
| `libpgm-5.3-0t64` 5.3.128~dfsg-2.1+b1 | `libpgm-5.3.so.0` | LGPL-2.1 | `libpgm-5.3-0t64.copyright.txt` |
| `libpixman-1-0` 0.44.0-3 | `libpixman-1.so.0` | see the file | `libpixman-1-0.copyright.txt` |
| `librabbitmq4` 0.15.0-1+deb13u2 | `librabbitmq.so.4` | Expat | `librabbitmq4.copyright.txt` |
| `librav1e0.7` 0.7.1-9+b2 | `librav1e.so.0.7` | BSD-2-clause | `librav1e0.7.copyright.txt` |
| `librist4` 0.2.11+dfsg-1 | `librist.so.4` | BSD-2-clause | `librist4.copyright.txt` |
| `librsvg2-2` 2.60.0+dfsg-1+deb13u1 | `librsvg-2.so.2` | LGPL-2+ | `librsvg2-2.copyright.txt` |
| `libsharpyuv0` 1.5.0-0.1 | `libsharpyuv.so.0` | BSD-3-Clause | `libsharpyuv0.copyright.txt` |
| `libshine3` 3.1.1-2+b2 | `libshine.so.3` | LGPL-2 | `libshine3.copyright.txt` |
| `libsnappy1v5` 1.2.2-1 | `libsnappy.so.1` | BSD-3-Clause | `libsnappy1v5.copyright.txt` |
| `libsodium23` 1.0.18-1+deb13u1 | `libsodium.so.23` | ISC | `libsodium23.copyright.txt` |
| `libsoxr0` 0.1.3-4+b2 | `libsoxr.so.0` | LGPL-2.1+ | `libsoxr0.copyright.txt` |
| `libspeex1` 1.2.1-3 | `libspeex.so.1` | BSD-3-Clause | `libspeex1.copyright.txt` |
| `libsrt1.5-gnutls` 1.5.4-1+deb13u1 | `libsrt-gnutls.so.1.5` | MPL-2.0 | `libsrt1.5-gnutls.copyright.txt` |
| `libssh-4` 0.11.5-0+deb13u1 | `libssh.so.4` | LGPL-2.1+~OpenSSL | `libssh-4.copyright.txt` |
| `libssl3t64` 3.5.7-1~deb13u3 | `libcrypto.so.3`, `libssl.so.3` | Apache-2.0 | `libssl3t64.copyright.txt` |
| `libsvtav1enc2` 2.3.0+dfsg-1 | `libSvtAv1Enc.so.2` | BSD-3-Clause-Clear | `libsvtav1enc2.copyright.txt` |
| `libswresample5` 7:7.1.5-0+deb13u1 | `libswresample.so.5` | LGPL-2.1+ | `libswresample5.copyright.txt` |
| `libswscale8` 7:7.1.5-0+deb13u1 | `libswscale.so.8` | LGPL-2.1+ | `libswscale8.copyright.txt` |
| `libtasn1-6` 4.20.0-2+deb13u1 | `libtasn1.so.6` | see the file | `libtasn1-6.copyright.txt` |
| `libthai0` 0.1.29-2+b1 | `libthai.so.0` | LGPL-2.1+ | `libthai0.copyright.txt` |
| `libtheoradec1` 1.2.0~alpha1+dfsg-6 | `libtheoradec.so.1` | BSD-3-Clause | `libtheoradec1.copyright.txt` |
| `libtheoraenc1` 1.2.0~alpha1+dfsg-6 | `libtheoraenc.so.1` | BSD-3-Clause | `libtheoraenc1.copyright.txt` |
| `libtwolame0` 0.4.0-2+b2 | `libtwolame.so.0` | LGPL-2+ | `libtwolame0.copyright.txt` |
| `libudfread0` 1.1.2-1+b2 | `libudfread.so.0` | LGPL-2.1+ | `libudfread0.copyright.txt` |
| `libunistring5` 1.3-2 | `libunistring.so.5` | GPL-3+ | `libunistring5.copyright.txt` |
| `libva-drm2` 2.22.0-3 | `libva-drm.so.2` | Expat | `libva-drm2.copyright.txt` |
| `libva-x11-2` 2.22.0-3 | `libva-x11.so.2` | Expat | `libva-x11-2.copyright.txt` |
| `libva2` 2.22.0-3 | `libva.so.2` | Expat | `libva2.copyright.txt` |
| `libvdpau1` 1.5-3+b1 | `libvdpau.so.1` | Expat | `libvdpau1.copyright.txt` |
| `libvorbis0a` 1.3.7-3 | `libvorbis.so.0` | BSD-3-Clause | `libvorbis0a.copyright.txt` |
| `libvorbisenc2` 1.3.7-3 | `libvorbisenc.so.2` | BSD-3-Clause | `libvorbisenc2.copyright.txt` |
| `libvorbisfile3` 1.3.7-3 | `libvorbisfile.so.3` | BSD-3-Clause | `libvorbisfile3.copyright.txt` |
| `libvpx9` 1.15.0-2.1+deb13u1 | `libvpx.so.9` | BSD-3-Clause | `libvpx9.copyright.txt` |
| `libwebp7` 1.5.0-0.1 | `libwebp.so.7` | BSD-3-Clause | `libwebp7.copyright.txt` |
| `libwebpmux3` 1.5.0-0.1 | `libwebpmux.so.3` | BSD-3-Clause | `libwebpmux3.copyright.txt` |
| `libx11-6` 2:1.8.12-1 | `libX11.so.6` | see the file | `libx11-6.copyright.txt` |
| `libx11-xcb1` 2:1.8.12-1 | `libX11-xcb.so.1` | see the file | `libx11-xcb1.copyright.txt` |
| `libx264-164` 2:0.164.3108+git31e19f9-2+b1 | `libx264.so.164` | GPL-2+ | `libx264-164.copyright.txt` |
| `libx265-215` 4.1-2 | `libx265.so.215` | GPL-2+ | `libx265-215.copyright.txt` |
| `libxau6` 1:1.0.11-1 | `libXau.so.6` | see the file | `libxau6.copyright.txt` |
| `libxcb-dri3-0` 1.17.0-2+b1 | `libxcb-dri3.so.0` | see the file | `libxcb-dri3-0.copyright.txt` |
| `libxcb-render0` 1.17.0-2+b1 | `libxcb-render.so.0` | see the file | `libxcb-render0.copyright.txt` |
| `libxcb-shm0` 1.17.0-2+b1 | `libxcb-shm.so.0` | see the file | `libxcb-shm0.copyright.txt` |
| `libxcb1` 1.17.0-2+b1 | `libxcb.so.1` | see the file | `libxcb1.copyright.txt` |
| `libxdmcp6` 1:1.1.5-1 | `libXdmcp.so.6` | see the file | `libxdmcp6.copyright.txt` |
| `libxext6` 2:1.3.4-1+b3 | `libXext.so.6` | see the file | `libxext6.copyright.txt` |
| `libxfixes3` 1:6.0.0-2+b4 | `libXfixes.so.3` | see the file | `libxfixes3.copyright.txt` |
| `libxml2` 2.12.7+dfsg+really2.9.14-2.1+deb13u3 | `libxml2.so.2` | MIT-1 | `libxml2.copyright.txt` |
| `libxrender1` 1:0.9.12-1 | `libXrender.so.1` | see the file | `libxrender1.copyright.txt` |
| `libxvidcore4` 2:1.3.7-1+b2 | `libxvidcore.so.4` | GPL-2+ | `libxvidcore4.copyright.txt` |
| `libzmq5` 4.3.5-1+b3 | `libzmq.so.5` | MPL-2.0 | `libzmq5.copyright.txt` |
| `libzstd1` 1.5.7+dfsg-1 | `libzstd.so.1` | BSD-3-clause or GPL-2 | `libzstd1.copyright.txt` |
| `libzvbi0t64` 0.2.44-1 | `libzvbi.so.0` | GPL-2+ | `libzvbi0t64.copyright.txt` |
| `ocl-icd-libopencl1` 2.3.3-1 | `libOpenCL.so.1` | BSD-2-Clause | `ocl-icd-libopencl1.copyright.txt` |

The game itself is not included in `gtavcs-psp.zip`: its files come from your own copy.
