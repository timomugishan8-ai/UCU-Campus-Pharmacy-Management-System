# Login hero image (optional)

Place a PNG file named **`login_hero.png`** in this folder to use a photo-style
hero background on the login gate:

```
assets/
└── login_hero.png
```

The login screen loads it with `tk.PhotoImage` (standard library, no Pillow)
and draws a stippled navy wash over it before placing the white form card on
top. A landscape image around **900 x 620 px** or larger works best.

If the file is missing or unreadable, the login screen automatically falls
back to the code-drawn navy background, so the application still runs on a
fresh clone. No Pillow / third-party dependency is required.

Only PNG and GIF are supported by `tk.PhotoImage`. JPEG files must be
converted to PNG first.

**Note:** adding a binary asset to the repository requires group approval
under the project agreement (standard library and agreed files only). Until
then, this folder documents the intended location without committing an image.
