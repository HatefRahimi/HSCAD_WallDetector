# README

## Compile the complete thesis

The entry point is `thesis_main.tex`. It loads the chapters, abbreviations,
bibliography and the supplied LME template. The complete source folder is required;
uploading the main file alone leaves its dependencies missing.

For Overleaf, upload `thesis-overleaf.zip` from the repository root as a new project.
The archive places `thesis_main.tex` at the project root and includes the chapter
files, generated tables, bibliography, template files and logos. Set the main document to
`thesis_main.tex` and select pdfLaTeX for routine online builds. The template also
supports XeLaTeX and LuaLaTeX. The bibliography uses Biber.
If an older upload has left auxiliary files behind, use Recompile from scratch.
The archive contains the current sources and must be regenerated after edits.

For a local TeX Live installation with pdfLaTeX, latexmk and Biber, run from the
repository root:

```bash
cd thesis
latexmk -pdf -interaction=nonstopmode -halt-on-error thesis_main.tex
```

The output is `thesis_main.pdf`. A complete build was also verified with Tectonic
and the Biber version matching its bundled biblatex. Open draft notes identify
missing experiments and do not prevent PDF output.

## Regenerate the reported tables

From the full repository root, run:

```bash
python3 scripts/export_thesis_tables.py --config configs/default.yaml
python3 scripts/check_citations.py
```

The exporter reads only recorded public audit metrics and the configured class
mapping. Its outputs are placed under `results/tables/` and loaded by the thesis.
The upload archive includes these outputs under its own `results/tables/` folder.

## Limited online compile time

Draft notes use plain text, without TikZ. Unused TikZ loads and duplicate package
loads have been removed. Online time limits still depend on the provider's build
environment. The locally compiled `thesis_main.pdf` is available directly if an
online build times out.

## Introduction

This is the LME thesis template. It supports English and German, different types of theses as well as pdflatex and lualatex. For this reason, some configuration has to be done in `thesis_main.tex` before you can start.

## Thesis type

You can use this template for Bachelor's and Master's theses as well as dissertations. You need to set a parameter to change the thesis type. Look for the %CONFIG tag in `thesis_main.tex`. These are the places you need to change. For dissertations, you also need to use a different kind of title page, so please fill out the correct one.

## Language

By default, the template creates an English document. If you want/need to write a German document, check the %LANGUAGE tags in the main tex file - these are the places you need to change. The legal note ("Ich versichere...") has to be in German.

## Engine

The template supports pdfLaTeX and luaLaTeX, if the later is preferred the TeX Live version must be 2020 (or above). Both engines may produce a slightly different output (e.g. with a slightly different font).
