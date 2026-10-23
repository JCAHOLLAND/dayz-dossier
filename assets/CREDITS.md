# Image sources

## Survivor portraits

21 fictional survivor portraits generated with the built-in imagegen tool, saved locally as `survivor.png` and `survivor-01.png` through `survivor-20.png`. Prompt and variant descriptions are in `portrait-generation.json`. These illustrations do not represent actual players, character appearance, equipment or location.

## Weapon images

These are actual DayZ Standalone in-game screenshot/cutout images sourced from the DayZ Wiki. `weapon-sources.json` records the exact weapon name, article URL, file description page, original URL, copyright notice and available file description for each image. DMR uses the user-supplied `M14.webp`, verified against the M14 image linked from the Standalone DMR article. Other game images were downloaded unchanged; PNG/WebP are the original response formats. They are scaled proportionally only when displayed.

Game imagery is copyrighted by Bohemia Interactive. This local, noncommercial game information dashboard uses screenshots under [Bohemia’s Game Content Usage Rules](https://www.bohemia.net/en/community/game-content-usage-rules). The wiki's [game copyright template](https://dayz.fandom.com/wiki/Template:Copyright_game) reserves the publisher’s underlying rights; these images are not claimed to be unrestricted or CC-licensed game assets. Wiki community text licensing does not override those rights. Source links appear on the weapon cards. No game files were extracted.

This project is unofficial and is neither affiliated with nor endorsed by Bohemia Interactive. DAYZ and associated game designs belong to their respective owners.

There is no verified asset for every imported weapon. In particular, the 2024 modded SCAR-H/SCAR-16 and RPK-16 records are not silently mapped to modern vanilla weapons or generic rifles. Missing exact images show an explicit text-only state.

The user-supplied [MyDayZ SCAR-H PR page](https://db.mydayz.eu/database/weapons/firearms/assault-rifle/scar-h-pr/) identifies a specific modded Precision Rifle variant and lists no aliases. The imported 2024 feed only says `SCAR-H`; it does not establish that PR variant or the server mod. That candidate is therefore not mapped to the generic feed name.

The local `rpk16.webp` image was sourced from the [MyDayZ RPK16 page](https://db.mydayz.eu/database/weapons/firearms/machine-gun/rpk16/). Its product title, image alt and description identify the RPK-16. The source footer reserves rights and no general redistribution license was found, so that image is intentionally excluded from this public repository. The dashboard displays the weapon name without an image when the file is absent.
