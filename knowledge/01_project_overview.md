# CRISPR-Sim Project Overview

CRISPR-Sim is an interactive simulator that walks you through CRISPR-Cas9 gene editing from DNA input to protein-level outcomes. It is educational: it models where SpCas9 cuts, how cells might repair the break (NHEJ or HDR), and how sequence changes affect mRNA and protein.

## End-to-end workflow in the app

1. DNA Input — Paste valid DNA (A, T, C, G), or fetch a sequence from NCBI using an accession number.
2. DNA Viewer — Shows your sequence with color coding (A blue, T red, G yellow/amber, C green), base composition, and overall GC%.
3. PAM Scanner — Finds every NGG PAM for SpCas9. Each site can show a 20 nt guide RNA, GC% of the guide, and whether the guide is in the recommended GC window (about 40–60%).
4. Cut Simulation — Cas9 is modeled as a blunt double-strand break three base pairs upstream of the PAM start. The app shows the cut position and splits upstream/downstream sequence.
5. Repair — NHEJ removes a chosen number of bases at the cut (indels). HDR inserts a donor template you provide, optionally replacing a span of bases.
6. Analysis — The original and edited DNA are transcribed to mRNA and translated to protein. The app reports frameshift (indel length not divisible by three), premature stop codons (*), length change, and a short summary.

## Backend and data

The FastAPI backend validates DNA, runs PAM regex `[ATCG]GG`, computes cuts and repairs, and uses BioPython for transcription/translation. SQLite stores session metadata. NCBI fetch uses E-utilities over the network when you use the Fetch tab.
