# easyTOS!
easyTOS is a utility program for installing, running, and mounting TempleOS. Please note that this software is in the alpha stage of development, so bugs might occur.

![alt text](easytos.png "Screenshot")

## Prerequisites
 - Linux: easyTOS currently only works on Linux.
    - nbd Kernel Module
 - Python 3.11
    - tkinter
    - requests
 - QEMU
 - [OPTIONAL] VirtualBox

## Installing
```bash
$ git clone https://github.com/berserkware/easyTOS
$ cd easyTOS
$ sudo cp easytos.py /usr/bin/easytos
```

## Running/Using
You need to run easyTOS with sudo for it to work.
```bash
$ sudo easytos
```
### Options
 - NEW INSTALLATION: Downloads the TOS ISO, creates the VM, and runs it for you to install TOS on the disc.
 - Installation Selector: Selection installation
 - RUN: Runs the selected installtion.
 - MOUNT: Mounts the selected installation's disc to allow you transfer files between your computer and Linux.
 - UNMOUNT: Unmounts the installation's disc.
 - EXIT: Exits easyTOS.

## TODO
 - [DONE] Support for mulitple TOS VMs
 - [DONE] Graphical VM-configurator
 - [DONE] Graphical easyTOS-configurator
 - Support mounting other drives, like the D drive.
 - Terminal logging.
### Known Bugs
 - Mounting multiple drives at the same time might cause unexpected behaviour. This is becuase nbd0 is hard coded to be used when mounting drives.
