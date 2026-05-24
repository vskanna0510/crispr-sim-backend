# DNA, RNA, Protein, and Reading Frame

## DNA basics

DNA is a double-stranded polymer of four nucleotides: adenine (A), thymine (T), cytosine (C), and guanine (G). In the app, only single-stranded sequence is edited for simplicity; bases must be A, T, C, or G after whitespace is removed.

## From DNA to mRNA (transcription)

In the simulation, transcription follows the standard complement rule for the coding strand as given: A→U, T→A, C→G, G→C in the RNA product. The app shows mRNA as a string of A, U, C, G.

## From mRNA to protein (translation)

Translation reads mRNA in non-overlapping triplets called codons. Each codon maps to one amino acid or a stop signal. Stop codons are often written as * in the protein string. The app trims DNA length to a multiple of three before translation so codons align.

## Frameshift

If insertions or deletions change the total length by a number not divisible by three, every codon after the edit shifts. That usually changes the entire downstream amino acid sequence and can create early stop codons. CRISPR-Sim flags this as a frameshift when |length difference| mod 3 is not zero.

## GC content

GC% is the percentage of G and C bases in a window. For guide RNAs, mid-range GC (often cited around 40–60% for SpCas9 guides in many setups) is marked “recommended” in the app; very low or very high GC may be less favorable in practice.

## DNA “sequencer” in the educational sense

The app is not a laboratory sequencer. It is a sequence viewer and analyzer: it displays bases, scans motifs, and simulates edits. Real sequencing produces reads from instruments; here you provide sequence or fetch from NCBI.
