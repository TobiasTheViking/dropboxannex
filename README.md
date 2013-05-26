dropboxannex
=========

Hook program for gitannex to use dropbox as backend

# Requirements:

    python2

Credit for the Dropbox api interface goes to Dropbox.

# Install
Clone the git repository in your home folder.

    git clone git://github.com/TobiasTheViking/dropboxannex.git 

This should make a ~/dropboxannex folder

# Setup
Run the program once to make an empty config file

    cd ~/dropboxannex; python2 dropboxannex.py

Edit the dropboxannex.conf file. Add your dropbox.co.nz username, password and folder name.

# Commands for gitannex:

    git config annex.dropbox-hook '/usr/bin/python2 ~/dropboxannex/dropboxannex.py'
    git annex initremote dropbox type=hook hooktype=dropbox encryption=shared
    git annex describe dropbox "the dropbox library"
