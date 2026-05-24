# App Features and On-Screen Outputs

## What each screen shows

Home: marketing-style overview and Start Simulation button.

DNA Input: validation rules (A/T/C/G only), demo HBB sequence loader, NCBI fetch with example accessions.

DNA Viewer: length, GC%, optional session id prefix, base composition bar, color-coded sequence with legend, Scan PAM Sites CTA.

PAM Scanner: count of PAMs, cards with PAM text, positions, gRNA, GC bar, badges (Recommended / Low GC / No gRNA), selection highlight, Simulate Cut when a site is selected.

Cut Simulation: selected gRNA recap, explanation of cut math, optional sequence preview with PAM highlight and vertical cut marker, cut result with upstream/downstream snippets.

Repair: NHEJ with deletion slider and frame note; HDR with donor field and replacement length; Apply & Analyse runs comparison.

Analysis: gradient summary banner, alert cards for frameshift or stop or “no major mutations”, sequence stats including repair type, protein and mRNA comparison boxes, copy FASTA or raw sequence.

## Error behavior

Network errors show as red banners or snackbars. Invalid DNA fails validation before hitting some API calls.

## API documentation

The deployed backend exposes interactive Swagger at /docs for trying endpoints manually.
