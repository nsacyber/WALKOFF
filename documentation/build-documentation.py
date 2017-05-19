#!/usr/bin/env python3

# Please see README.txt in this folder for instructions.

import os
import glob

files = glob.glob("source/*.html")

header = open("header.html").read()
footer = open("footer.html").read()

for inFilename in files:
    fin = open(inFilename)
    content = fin.read()

    outFilename = "build/" + os.path.basename(inFilename)
    fout = open(outFilename, 'w')
    fout.write(header + content + footer)
    
    fin.close()
    fout.close()
    
    print(inFilename + " -> " + outFilename)
