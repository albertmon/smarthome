#!/usr/bin/env python

import unidecode
for i in ("artists", "albums", "composers"):
    f = open(f"../slots/{i}", "r")
    for x in f:
        y = unidecode.unidecode(x)
        if x != y:
            print(f"org:<{x}> != <{y}>:decoded")

    

# End of File
