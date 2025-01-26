# df-setup

A small application for setting up a collection of applications that are configured via "dotfiles."

Assumes that each application's dotfiles are organized as follows:

```
.
├── dots/       # Actual dotfiles in this directory.
├── README.md   # (optional)
├── install.sh  # (optional)
└── setup.sh    # Sets up the applications dotfiles; e.g. symlinks dots/app.config to ~/.config/app.config.

```
