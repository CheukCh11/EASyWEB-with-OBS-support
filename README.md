# EASyWEB-with-OBS-support
An EASyPLUS emulator, [EASyWEB](https://github.com/easyweb-project/easyweb), with add-on scripts that have been ported for OBS support.

- **`patch_obs.py`** adds two new modes to your copy of EASyWEB:
  - `?obs` is a clean display (just the CGEN screen, no sidebar or menu) for an OBS Browser Source.
  - `?remote` is a control panel that drives the display. Use it as an OBS Custom Browser Dock.
- **`patch_eom.py`** makes EOM detection tolerant of lost bursts, so live URL/mic streams no longer wait minutes for an alert to "finish" when one EOM burst was missed.

This repo contains **only the patch scripts**, not EASyWEB itself. You patch your own download of the original file.

> Not affiliated with or endorsed by the EASyWEB project, Trilithic, or VIAVI. Hobbyist use only, not for real alerting or life-saving information. See the original project's own disclaimer about EAS tones.
> The patch scripts were written with the help of AI (Claude) and are lightly tested. Please report problems in Issues.

## Requirements

- Python 3 (`python --version`; use `python3` if `python` isn't found)
- OBS with browser support. Windows and macOS builds have it; many Linux builds don't, so Custom Browser Docks may not work there.

## How to use

1. Download EASyWEB's HTML file from the project's GitHub page (click **Raw** or the download icon and save it; don't save the web page itself). Put it in a folder together with `patch_obs.py` and `patch_eom.py`.
2. Open a terminal/command prompt **in that folder** and run (replace `main.html` with the real file name):
   ```
   python patch_obs.py main.html easyweb-obs.html
   python patch_eom.py easyweb-obs.html easyweb-obs.html
   ```
3. In the same folder/window, start a small local server and keep the window open while you stream:
   ```
   python -m http.server 8000
   ```
4. In OBS, add a **Browser** source:
   - URL: `http://localhost:8000/easyweb-obs.html?obs`
   - Width/Height: the resolution you pick in the app (e.g. 1440 x 1080); FPS: same as your OBS canvas
   - Tick **Control audio via OBS**
   - Untick **Shutdown source when not visible** and **Refresh browser when scene becomes active**
5. **Docks > Custom Browser Docks**: name it anything and use the URL `http://localhost:8000/easyweb-obs.html?remote`, then dock it wherever you like.
6. The dock should say **Connected to the display**. Pick Import, Stream or URL at the top and control everything from the panel.

## Troubleshooting

- **"Waiting for the display"**: make sure only one `?obs` page is open and both URLs are typed exactly. Fallback: open `?obs` in its own Chrome window and `?remote` in another tab of the same Chrome, then use Window Capture on the `?obs` window.
- **After replacing the HTML file**: restart the server and press "Refresh cache of current page" on the browser source.
- **A patch script says "Could not patch"**: the EASyWEB version changed and an anchor moved. Open an issue with the message.
- Mic, screen share and camera may not work inside OBS. Record and Full Screen are hidden in the panel because OBS records.

## License

The scripts in this repo are under the MIT License (see `LICENSE`). EASyWEB and its fonts and images belong to their own authors and licenses; none of that is included here.

## AI Notice
I am quite afraid that this DOES use artificial intelligence.
