# rabbit

## Category
Misc

## Points
Dynamic starting at 500, ending at 100

## Description
Can you find Babushka's missing vodka? It's buried pretty deep, like 1000 steps, deep.

Author: Crem + z3kxTa

Files: `flag.txt`

## Keywords
Recursive zip, bzip2, gunzip, unzip, bash, base64

## Notes
I looked at the initial file using `file`:

```
$ file flag.txt
flag.txt: bzip2 compressed data, block size = 900k
```

So I copied the file to `flag.bz2` and used `bzip2` to unzip it:

```
$ cp flag.txt flag.bz2
$ bzip2 -dk flag.bz2
```

I then ran `file` over the generated file:

```
$ file flag
flag: bzip2 compressed data, block size = 900k
```

Another compressed file! The description suggests there's a thousand of these, so I wrote a bash script to solve it. Each time it found an *Unknown file type* I added that type to the script. The final script was:
```bash
#!/bin/bash

name=flag.txt
num=0
over=0
command=""
extension=""
pipeit=0

while [ $over -eq 0 ]
do
  res=$(file $name | grep "bzip2 compressed" | wc -l)
  if [ $res -gt 0 ]
  then
    command="bzip2 -dk"
    extension=bz2
  elif [ $(file $name | grep "Zip archive" | wc -l) -gt 0 ]
  then
    command="unzip -p"
    extension=.zip  
    pipeit=1
  elif [ $(file $name | grep "XZ compressed" | wc -l) -gt 0 ]
  then
    command="unxz"
    extension=xz
  elif [ $(file $name | grep "gzip compressed" | wc -l) -gt 0 ]
  then
    command="gunzip"
    extension=gz
  else
    echo Unknown file type: $(file $name)
    over=1
  fi

  if [ $over -ne 1 ]
  then
    echo Doing $name
    cp $name flag${num}.$extension
    name=flag${num}
    ((num=num+1))
    if [ $pipeit -eq 0 ]
    then
      $command ${name}.$extension
    else
      $command ${name}.$extension > $name
    fi
    pipeit=0
  fi
done
```
The `pipeit` variable is to stop zip files from creating `flag.txt` files each time, and instead use the name I assigned. Other programs extract as the original file name minus the extension.

This ran and gave me an ASCII file to finish:
```
...
Doing flag987
Doing flag988
Doing flag989
Doing flag990
Doing flag991
Doing flag992
Doing flag993
Doing flag994
Doing flag995
Doing flag996
Doing flag997
Doing flag998
Unknown file type: flag999: ASCII text
```

Using `cat` on `flag999` gave me something that looked like *base64*, so I ran that through the `base64` decoder:
```
$ cat flag999
RFVDVEZ7YmFidXNoa2FzX3YwZGthX3dhc19oM3IzfQ==
$ cat flag999 | base64 -d
DUCTF{babushkas_v0dka_was_h3r3}
```

This gave me the flag.
