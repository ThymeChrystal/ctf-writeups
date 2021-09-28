# retro

# Category
Forensics

## Points
Dynamic points starting at 500, ending at 100

## Description
Our original logo was created in paint, I wonder what other secrets it hides?

Author: QUTWH

File: `og.jpg`

## Keywords
jpg, exif, image

## Notes
The `og.jpg` was an image of the 'orginal logo'.
![Original Logo](./og.jpg)

This one was pretty straightforward one. The first thing I do when I get an image is run `exiftool` to see what information we can get. The flag was in the Exif information in the `Creator` tag:
```
$ exiftool od.jpg
...
Derived From Instance ID        : xmp.iid:7f7157ae-f9a9-4b39-ac8b-368dc10e4af8
Derived From Document ID        : xmp.did:7f7157ae-f9a9-4b39-ac8b-368dc10e4af8
Derived From Original Document ID: uuid:65E6390686CF11DBA6E2D887CEACB407
Derived From Rendition Class    : proof:pdf
History Action                  : saved, saved
History Instance ID             : xmp.iid:7f7157ae-f9a9-4b39-ac8b-368dc10e4af8, xmp.iid:debb54d2-eef4-482d-8fea-b5ad9a904da8
History When                    : 2020:06:16 17:48:09+10:00, 2020:06:16 17:51:24+10:00
History Software Agent          : Adobe Illustrator CC 2015 (Macintosh), Adobe Illustrator CC 2015 (Macintosh)
History Changed                 : /, /
Manifest Link Form              : EmbedByReference
Manifest Reference File Path    : /Users/h4sh/Downloads/DownUnderCTF_Paint.png
Manifest Reference Document ID  : 0
Manifest Reference Instance ID  : 0
Ingredients File Path           : /Users/h4sh/Downloads/DownUnderCTF_Paint.png
Ingredients Document ID         : 0
Ingredients Instance ID         : 0
Startup Profile                 : Web
Producer                        : Adobe PDF library 10.01
Creator                         : DUCTF{sicc_paint_skillz!}
Profile CMM Type                : Linotronic
Profile Version                 : 2.1.0
Profile Class                   : Display Device Profile
Color Space Data                : RGB
Profile Connection Space        : XYZ
Profile Date Time               : 1998:02:09 06:49:00
Profile File Signature          : acsp
Primary Platform                : Microsoft Corporation
...
```
