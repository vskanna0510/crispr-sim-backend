# CRISPR-Cas9 Concepts in CRISPR-Sim

## PAM

SpCas9 requires a protospacer adjacent motif (PAM) on the non-target strand. In this project the PAM pattern is NGG: any of A/T/C/G followed by GG. The scanner reports each match with start/end indices in the pasted sequence.

## Guide RNA (gRNA)

The app extracts twenty bases immediately upstream of the PAM as the guide sequence (standard SpCas9 spacer length). If the sequence is too short before the PAM, a guide may be missing.

## Cut site

The simulated cut is exactly three base pairs before the PAM start index (PAM_start − 3). That matches the common teaching model for blunt DSB placement relative to the PAM.

## NHEJ

Non-homologous end joining re-ligates broken ends and often introduces small insertions or deletions. In the simulator you choose a deletion size (1–10 bp) removed around the cut; the app notes in-frame vs out-of-frame deletions (multiple of three or not).

## HDR

Homology-directed repair uses a donor template. The app lets you paste donor DNA and choose how many bases at the cut are replaced before insertion. HDR efficiency depends on many real-world factors; the simulator only models the sequence outcome you configure.

## Interpreting analysis output

Original vs edited protein strings are compared. Premature stop means a stop codon appears earlier in the edited protein than in the original. The summary line aggregates frameshift, stop, and length change in plain language.
