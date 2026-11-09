# PyBibX integration

SāhityaLab treats [PyBibX](https://github.com/valdecy/pybibx) as the specialist bibliometric and scientometric engine. PyBibX supports Scopus exports (`.bib` and `.csv`), Web of Science (`.bib`), PubMed (`.txt`) and OpenAlex (API JSON and standard website CSV), along with source comparison, duplicate handling, metadata normalisation, exploratory analysis, author metrics, co-authorship/co-citation/coupling networks, thematic and temporal analysis, and other scientometric functions. Consult its current README and examples for the precise capabilities of the installed release.

## Install and launch

```bash
pip install -e '.[bibliometrics]'
sahitya bibliometrics launch
```

Python equivalent:

```python
import pybibx
pybibx.web_app()
```

The upstream README documents `pybibx.web_stop()` to stop the local service. SāhityaLab wraps this as:

```bash
sahitya bibliometrics stop
```

## Prepare a SāhityaLab source manifest

```bash
sahitya bibliometrics prepare scopus.csv export_wos.bib --output-dir outputs/pybibx
```

The manifest lists input file paths, imported record count, and normalised metadata. Keep the raw exports unchanged and select the original files in the PyBibX workbench. The manifest is a provenance record, not a PyBibX-native dataset and not a claim that analysis was run.

## Important format note

SāhityaLab's common article importer supports CSV, JSON, BibTeX and PubMed MEDLINE `.txt`. Its OpenAlex JSON mapping handles the common API `results` format and inverted-index abstracts. PyBibX may support additional or evolving structures beyond this normalisation layer. For source formats not yet handled by SāhityaLab, use the original export directly in PyBibX and preserve it in the review project's `data/raw/` directory. Avoid converting a rich export into a lossy common CSV merely to pass it through SāhityaLab.

## Licensing and AI keys

PyBibX is a separately licensed project; review its current licence and notices before redistribution. Some AI-powered capabilities in PyBibX require external API credentials. Configure those within the PyBibX workflow and follow the service and institutional policies that apply to unpublished research data. SāhityaLab does not inherit or relicense PyBibX.
