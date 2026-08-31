# Practical Visuomotor Robot-Learning Workflow

This directory builds an internal handover manual for future LIRMM students:

> **Practical Workflow for Testing Visuomotor Robot Learning Systems**

The intended reader knows the basics of Python, machine learning, ROS, and
robotics, but may not yet have run a complete learning-based manipulation
experiment. The manual explains a reusable methodology rather than prescribing
one exact model or robot. Luca Vogelgesang's Diffusion Policy project is used as
a concrete example throughout.

The five chapters cover:

1. benchmark definition, interfaces, and MuJoCo validation;
2. teleoperation and demonstration recording;
3. dataset interfaces, training, and model selection;
4. staged physical deployment and safety;
5. evaluation, diagnosis, and iteration.

Appendix A provides the complete Touch/OpenHaptics installation. Exact project
commands remain in `README_ENV.md`, `README_SERVER.md`, and `README_CODE.md`.

The source is split into chapters for maintenance, while the deliverable is one
searchable PDF.

Build from this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Clean generated LaTeX files:

```bash
latexmk -C main.tex
```

The expected output is [`main.pdf`](main.pdf). Update the version and reference
Git commit on the title/front-matter pages when procedures or interfaces change.

The PDF is intentionally kept in the repository so a new intern can read the
manual before installing LaTeX. Generated auxiliary files are ignored.
