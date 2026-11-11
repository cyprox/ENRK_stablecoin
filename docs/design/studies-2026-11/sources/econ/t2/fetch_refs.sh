#!/bin/sh
# Why: re-download the public reference data (GET only) into ./web; analysis via ref_extract.py
mkdir -p web && cd web
curl -sL -m 90 -o pools.json https://yields.llama.fi/pools
curl -sL -m 90 -o lendborrow.json https://yields.llama.fi/lendBorrow
curl -sL -m 60 -o kaskad.json https://api.llama.fi/protocol/kaskad
curl -sL -m 60 -o liquity_v1_readme.md https://raw.githubusercontent.com/liquity/dev/main/README.md
curl -sL -m 60 -o liquity_v1_faq.html https://docs.liquity.org/liquity-v1/faq/borrowing
curl -sL -m 60 -o liquity_v2_faq.html https://docs.liquity.org/faq/borrowing
