# This finds all files and folders, and build
# a set of readme.md files and an index of
# keywords in this directory
#
# (c) ThymeChrystal 2021
import os
import re
import collections
from shutil import copyfile
from string import ascii_uppercase

def lower_key(pair):
  key, value = pair
  return (key.lower(), value)

start_path = "./"

dirs = []
files = []
print("Looking for directories...")
for root, dir_name, file_name in os.walk(start_path):
  for d in dir_name:
    # Exclude hidden files - e.g. .git
    if d.startswith(".") or root.startswith("./."):
      continue
    dirs.append(os.path.join(root, d))
    print(f" + Adding {d}")
  
# Build the top-level README.md
print("Creating top-level README.md")
copyfile("./README-template.txt", "./README.md")
with open("./README.md", "a") as rmd:
  for d in dirs:
    rmd.write(f"* [{os.path.basename(d)}]({d})\n")

# Now do the READMEs for each subdirectory
for d in dirs:
  print(f"Creating readme in {d}...")
  template = os.path.join(d, "README-template.txt")
  md_file = os.path.join(d, "README.md")
  dir_name = os.path.basename(d)
  if os.path.isfile(template):
    copyfile(template, md_file)
  else:
    with open(md_file, "w") as mdf:
      mdf.write(f"# {dir_name}\n")
      mdf.write(f"Write-ups for {dir_name}\n\n")
  with open(md_file, "a") as mdf:
    for root, dirn, filen in os.walk(d):
      for f in filen:
        if f.lower().endswith(".md") and os.path.basename(f).lower() != "readme.md":
          print(f" + Adding {f}")
          files.append(os.path.join(root, f))
          mdf.write(f"* [{os.path.splitext(f)[0]}](./{f})\n")

# Finally, build the index
print("Building index...")
index = {}

# Create an alphabetical index into the word index
# to show at thw top of the list for quick access
alpha_refs = {}
for i in ascii_uppercase:
  alpha_refs[i] = ''

for f in files:
  with open(f, "r") as in_file:
    text = in_file.readlines()
    reading_kw = False
    for line in text:
      line = line.strip()
      if reading_kw:
        next_title = re.search("^#", line)
        if next_title == None:
          words = line.split(",")
          for w in words:
            w = w.strip()
            if w == '':
              continue
            index.setdefault(w, []).append(f)
            curr_alpha = alpha_refs[w[0].upper()]
            if curr_alpha == '' or w.lower() < curr_alpha.lower():
              alpha_refs[w[0].upper()] = w
        else:
          break
      else:
        kw_title = re.search("^#+\s*[Kk]eywords\s*$", line)
        if kw_title != None:
          reading_kw = True

# Sort the index and write
index = collections.OrderedDict(sorted(index.items(), key=lower_key))
copyfile("index-template.txt", "index.md")
with open('index.md', "a") as i:
  # Write alphabetical links at the top of the page
  i.write('\n---\n\n')
  for k, v in alpha_refs.items():
    if v == '':
      i.write(f"{k} ")
    else:
      val = v.replace(' ', '-').replace('/', '')
      i.write(f"[{k}](#{val.lower()}) ")
  i.write('\n\n---\n\n')

  # Write the word index
  for k, v in index.items():
    print(f" + Adding entries for {k}")
    i.write(f"### {k}\n")
    for f in v:
      name = f.replace("./", "")
      name = os.path.splitext(name)[0]
      name = name.replace("/", " - ")
      print(f"   - Including {f}")
      i.write(f"* [{name}]({f})\n")

