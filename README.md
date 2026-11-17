# Dark-matter research

[![Tests](https://github.com/bomberJV/dark-matter-research/actions/workflows/tests.yml/badge.svg)](https://github.com/bomberJV/dark-matter-research/actions/workflows/tests.yml) · [Open it on brandonfhuang.com](https://brandonfhuang.com/projects/papers/dark-matter-2026/)

- [Dark Matter, by Its Consequences](manuscript.md) compares halo profiles against SPARC rotation curves. The Python analysis, input data, figures and [paper PDF](web/dark-matter-2026.pdf) are included. [Reproduce the fits and figures](REPRODUCING.md).
- [What predicts a galaxy's acceleration?](notes/sparc-pilot.md) reports the earlier multivariate pilot. The [original project note](notes/pilot-source.md) records its results. Its original analysis code is unavailable.
- [Beyond rotation curves](notes/beyond-rotation-curves.md) sets out the related research proposal.
- [One event, many explanations](lz-event-audit/README.md) puts 24 published explanations of the LZ 248 keV event under one halo, detector model and likelihood, with validation against seven independent groups' numbers.

To read the interactive paper, run `python -m http.server 8000` from this directory and open [the web edition](http://localhost:8000/web/).

## License

Created by Brandon Frank Han-Chween Huang ([brandonfhuang.com](https://brandonfhuang.com)).

- **Code** (scripts, styles, page markup, tests and tools): [Apache License 2.0](LICENSE). Keep the [NOTICE](NOTICE) file with any copy or derivative.
- **Writing, figures, papers, results and narration recordings**: [CC BY 4.0](LICENSE-CC-BY-4.0.txt). Credit “Brandon Frank Han-Chween Huang” and link to https://brandonfhuang.com or this repository.
- **Third-party files** keep their own licenses:
  - `data/` holds the public SPARC files of Lelli, McGaugh & Schombert (2016). Their creators keep their rights; see [REPRODUCING.md](REPRODUCING.md).
