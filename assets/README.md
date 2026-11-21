# Login hero image

`login_hero.png` in this folder is the photo background for the login gate.
It shows the UCU Allan Galpin University Health Centre and was converted
from a JPEG supplied by the group to PNG at 1000 x 664 px, because
`tk.PhotoImage` cannot read JPEG without Pillow.

The login screen loads it with `tk.PhotoImage` (standard library, no Pillow)
and draws a stippled navy wash over it before placing the white form card on
top. A landscape image around 900 x 620 px or larger works best.

If the file is missing or unreadable, the login screen automatically falls
back to the code-drawn navy background, so the application still runs on a
fresh clone. No Pillow / third-party dependency is required.

Only PNG and GIF are supported by `tk.PhotoImage`. JPEG files must be
converted to PNG first. The original JPEG is kept outside the repository as
a design reference and is not committed.

## `ucu_logo.png`

The official UCU logo lockup (crest + "UGANDA CHRISTIAN UNIVERSITY" +
tagline) used in the white branding header of the login card. Supplied as
`UCU_logo.PNG` in Downloads and resized to 334 x 84 px so it fits the
366 px-wide card. If the file is missing, the login falls back to a
Canvas-drawn teal pill logo.

## `ucu_crest.png`

The crest-only crop of the official logo (56 x 68 px), used in the narrow
application sidebar instead of the old drawn teal pill. The full lockup is
too wide for a 250 px sidebar, so the crest is paired with the app's own
"UCU Pharmacy / Management System" labels. `gui/main_window.py` falls back
to the drawn pill if this asset is missing.
