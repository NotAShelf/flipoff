<!--markdownlint-disable MD013 MD033 MD041 -->

<div id="doc-begin" align="center">
  <h1 id="header">flipoff</h1>
  <p>Congratulations. You have reached the logical conclusion of your relationship with modern computing.</p>
</div>

<p align="center">
  <br/>
  <img
    alt="Latest demo for flipoff with Walter White from Breaking Bad"
    src="./assets/demo.png"
    width="800px"
  >
  <br/>
</p>

## Synopsis

flipoff is a _fully offline_ Python utility that leverages _sophisticated
computer vision_ to _solve the oldest problem in human-computer interaction_:
the fact that your machine is still running when you no longer wish it to be. It
monitors your webcam feed for a specific, globally recognized gesture of
structural disapproval, also known as the middle finger, and immediately
executes a system shutdown via D-Bus.

> [!IMPORTANT]
> **Disclaimer**
>
> I am not responsible if you use this while in a Zoom meeting and accidentally
> flip off your coworkers. Granted, that would be hilarious and I want to hear
> about it but I don't accept responsibility about any hurt feelings or lost
> work.

## Motivation

We live in an era of digital friction. Imagine you have just sat through a
three-hour "sync" meeting that could have been an email. Or that your IDE has
decided that your _perfectly valid_ syntax is actually a personal affront.
Perhaps rust-analyzer has safely leaked memory again. Your computer is just
standing there, even.

**YOU HATE IT ALL**.

For those kind of moments, conventional exit strategies are insufficient and
meaningless. They lack energy. They lack... catharsis. Thus, **flipoff** was
made. Built on three core pillars of modern engineering:

- Efficiency: Why move a mouse several inches when you can simply extend a
  single digit from the comfort of your keyboard?
- Emotional Honesty: Your computer should know exactly how you feel about its
  latest "Mandatory Update" during a presentation. Hate. Let me tell you about
  _hate_.
- The Final Word: There is no greater feeling of power than watching your
  monitor go black at the exact moment of your peak indignation.

We have spent decades teaching computers to understand our speech and our touch.
It was about time we taught them to understand our boundaries.

## Building & Development

### Prerequisites

- Linux machine running with D-Bus (primarily Systemd-based distributions)
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Bunch of system libraries (see `shell.nix` for a list)
- A working webcam

Or, if you're sane, Nix. For now a very simple Nix development shell is provided
in `shell.nix`. Use either `direnv allow` or `nix-shell` to get the
dependencies.

### Running

[uv]: https://docs.astral.sh/uv/

This project is built with Python 3.11 (later versions may misbehave) and [uv]
as the Python package manager. To run it, you may simply clone the repository
and install it:

```bash
# Install the package
$ uv pip install -e .

# With webcam
$ flipoff

# With debug overlay for landmarks
$ flipoff --debug

# Dry run (no actual poweroff)
$ FLIPOFF_DRYRUN=1 flipoff
```

For development, `uv run flipoff` works without installing.

### CLI Options

| Option       | Default        | Description                         |
| ------------ | -------------- | ----------------------------------- |
| `--gesture`  | `flipping_off` | Gesture to detect                   |
| `--event`    | `poweroff`     | Event to trigger                    |
| `--headless` | off            | Hide GUI window                     |
| `--camera`   | `0`            | Camera index                        |
| `--cooldown` | `2.0`          | Cooldown between triggers (seconds) |
| `--debug`    | off            | Show landmark debug overlay         |

### Obtaining the Models

To run this program, **you will need Google's MediaPipe models** downloaded
somewhere. This is done automatically inside the Nix devshell when you run
`nix-shell`, but to run this program on different distributions or without Nix
you need to get the models.

[here]: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

<!--markdownlint-disable MD059-->

You may find the models [here]. Simply download them to a location of your
choosing, and point `FLIPOFF_MODEL_PATH` environment variable to the full
download path.

<!--markdownlint-enable MD059-->
