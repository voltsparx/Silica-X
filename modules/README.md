# Modules Catalog

Release: v9.3.0 (Theme: Lattice)

Generated index for module-like capabilities discovered under `intel-sources/`.

- `index.json`: full catalog with capability tags, scoring, and scope hints
- `plugin-modules.json`: plugin-like subset
- `filter-modules.json`: filter-like subset

Refresh from CLI:
- `python sylica-x.py modules --sync`

Advanced query examples:
- `python sylica-x.py modules --search dns --sort-by power_score --descending`
- `python sylica-x.py modules --kind plugin --tag identity --min-score 55`
