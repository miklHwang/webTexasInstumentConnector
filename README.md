# TI-ConnectMC

A Minecraft-style web connector for graphing calculators. Plug a calculator into your computer, open the site in Chrome or Edge, and send files, receive variables, take screenshots, and back up or restore it. There's nothing to install.

**Site:** https://miklhwang.github.io/webTexasInstumentConnector/ (the landing page; the connector itself is at `webtilp.html`)

TI-ConnectMC is a reskin of [WebTILP](https://github.com/adriweb/tilibs/tree/exp2-full-emscripten) by Adriweb. The calculator engine is [tilibs](https://github.com/debrouxl/tilibs) and [hplp](https://github.com/debrouxl/hplp), compiled to WebAssembly. It is unchanged here; only the look, the branding and the hosting are different.

## Supported calculators

| Family | Models | Cable |
| --- | --- | --- |
| TI-84 Plus | TI-84 Plus, Silver Edition, C Silver Edition, CE, CE Python, TI-84 Plus T, TI-84 Evo, Evo-T | USB |
| TI-83 / TI-82 | TI-83 Premium CE (and Python Edition), TI-83 Evo, TI-82 Advanced (and Edition Python), TI-83, TI-83 Plus | USB; TI-83 and 83 Plus need SilverLink or GrayLink |
| TI-Nspire | Nspire, Clickpad, Touchpad, CX, CX CAS, CX II, CX II CAS, CX II-T, CM-C | USB |
| TI-89 / TI-92 | TI-89, TI-89 Titanium, TI-92, TI-92 Plus, Voyage 200 | TI-89 Titanium: USB; the others need SilverLink or GrayLink |
| Classic TI | TI-73, TI-80, TI-82, TI-85, TI-86 | SilverLink or GrayLink |
| HP Prime | G1, G2 | USB (WebHID) |
| NumWorks | Python scripts, device info, storage backup | USB (WebUSB) |

You need a Chromium-based browser (Chrome or Edge) on Windows, macOS, Linux, ChromeOS or Android. Firefox and Safari don't have WebUSB, WebHID or WebSerial.

## Themes

Open **Settings** to see every theme as a preview card:

- **Try a theme:** click its card. It stays on until you close the tab.
- **Keep it:** click **Set as default**. The site then opens with that theme on this device. A "Default" badge marks the current default.
- **Link to a theme:** add `?theme=` to the address, for example `webtilp.html?theme=cyberpunk`.

| Theme | Look |
| --- | --- |
| **Minecraft (Auto)** | Follows the device's light/dark setting. This is the default for a first visit. |
| **Minecraft Day** | Dirt background with light inventory panels. |
| **Minecraft Night** | Deepslate background with dark panels. |
| **Modern** | Clean and simple, in the spirit of Apple's apps. Frosted bars, rounded cards, switches, thin line icons. Follows light/dark. |
| **Cyberpunk** | A fan-made homage to Cyberpunk 2077: neon yellow, cyan and red, bevelled HUD frames, and a glitching logo. |
| **Dark Modern**, **Light Modern**, **Retro Terminal**, **Professional Light/Dark**, **Minimal** | The original WebTILP themes. |

To change the default for first-time visitors, edit `SITE_DEFAULT_THEME` in `webtilp/app.js`.

## The Minecraft theme

- **Extras:**
  - splash text next to the logo;
  - XP-bar progress bars;
  - achievement pop-ups when a transfer, screenshot, backup or restore succeeds;
  - optional button click sounds, turned on in Settings and off by default.

All textures are original pixel art, so no Mojang assets or resource pack are used. The fonts are Jersey 10 and Press Start 2P, both under the SIL Open Font License.

Where the themes live:

| Path | What it is |
| --- | --- |
| `webtilp/minecraft.css` | The theme stylesheet, loaded after `app.css` |
| `webtilp/index.html` | The title-screen landing page |
| `webtilp/mc/fonts/` | Self-hosted fonts and `OFL.txt` |
| `webtilp/mc/textures/` | 16×16 textures |
| `webtilp/mc/tools/make_textures.py` | Generates the textures and the favicon/app icons. Needs Pillow; run `python3 webtilp/mc/tools/make_textures.py` |
| `webtilp/themes/cyberpunk.css`, `webtilp/themes/modern.css` | The Cyberpunk and Modern stylesheets |
| `webtilp/themes/fonts/` | Rajdhani and Inter, with `OFL.txt` |
| `webtilp/app.js` | The "TI-ConnectMC extras" block (splash, achievements, click sounds), the `THEMES` list and the theme picker |

Internal names are left as upstream has them (the `webtilp.*` file names, element ids and storage keys), so upstream updates merge cleanly.

## Hosting (GitHub Pages)

The workflow `.github/workflows/build.webtilp.workflow.yml` builds the WebAssembly engine, runs the tests, and deploys the production build to GitHub Pages on every push to the default branch.

One-time setup on GitHub:

1. Go to **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**.
2. If the deploy job says the branch isn't allowed to deploy, go to **Settings → Environments → github-pages** and allow the default branch.

The first build compiles the dependencies from scratch and takes a while. Later builds reuse the cache.

## Pulling upstream updates

```sh
git remote add upstream https://github.com/adriweb/tilibs.git   # once
git fetch upstream exp2-full-emscripten
git merge upstream/exp2-full-emscripten
```

Conflicts usually land in `webtilp/app.js`, `webtilp/webtilp.html` or the `i18n/*.json` files, where the visible "WebTILP" text was renamed.

## Development

```sh
make -C webtilp test   # frontend unit tests and translation checks; needs node, python3 and a C++ compiler
```

The full build (`make -C webtilp prod`) needs the Emscripten toolchain and the prebuilt dependencies. CI sets both up; see the workflow file for the exact steps.

## Credits and license

- **WebTILP:** frontend and WebAssembly glue by Adriweb.
- **tilibs and TILP:** Lionel Debroux, Romain Liévin and the TILP contributors.
- **hplp:** HP Prime support, by Lionel Debroux.
- **NumWorks:** support through [Upsilon.js](https://github.com/Yaya-Cout/Upsilon.js) and [WebDFU](https://github.com/M4xi1m3/webdfu), both MIT.
- **Fonts:** Jersey 10 (The Soft Type Project Authors), Press Start 2P (The Press Start 2P Project Authors), Rajdhani (Indian Type Foundry) and Inter (The Inter Project Authors), all SIL OFL 1.1.
- **Icons:** [Feather](https://github.com/feathericons/feather) by Cole Bemis, MIT.

TI-ConnectMC is free software under the GNU General Public License, version 2; see [COPYING](COPYING). The individual libraries keep their own license files.

Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft. The Cyberpunk theme is a fan-made homage that uses no game assets; it is not affiliated with or endorsed by CD PROJEKT RED, and Cyberpunk 2077 is their trademark. The Modern theme is not affiliated with Apple. TI-ConnectMC is not affiliated with Texas Instruments, HP or NumWorks; their trademarks belong to their respective owners.
