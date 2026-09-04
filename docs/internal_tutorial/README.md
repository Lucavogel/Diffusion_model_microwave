# MuJoCo Simulation Tutorial

This directory builds an internal handover manual for future LIRMM students:

> **MuJoCo Simulation Tutorial: Teleoperation, Data Recording, and Policy Deployment**

The intended reader knows the basics of Python, machine learning, ROS, and
robotics, but may not yet have run this project. The manual stays close to the
implemented workflow and points to the maintained README files for exact
commands.

The four chapters cover:

1. understanding MuJoCo through a runnable example, then preparing and
   validating the project scene;
2. teleoperating the simulated robot with the Touch;
3. recording, replaying, and checking demonstrations;
4. training a checkpoint and deploying it first in simulation, then optionally
   on a physical robot.

Appendix A provides the complete Touch/OpenHaptics installation. Exact project
commands remain in `README_ENV.md`, `README_SERVER.md`, and `README_CODE.md`.
The runnable MuJoCo introduction is stored in `dp_mujoco/examples/`.

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
