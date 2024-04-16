# easyTOS!
easyTOS is a utility program for installing, running, and mounting TempleOS.

![alt text](easytos.png "Screenshot")

## Prerequisites
 - Linux: easyTOS currently only works on Linux.
 - Python 3.11
 - Tkinter
 - Requests
 - QEMU

## Installing
```bash
$ git clone https://github.com/berserkware/easytos
$ cd easytos
$ sudo cp easytos.py /usr/bin/easytos
```

## Running/Using
You need to run easyTOS with sudo for it to work.
```bash
$ sudo easytos
```
### Options
 - INSTALL/REINSTALL: Downloads the TOS ISO, creates the QEMU disc, and runs the VM for you to install TOS on the disc.
 - RUN: Runs TempleOS.
 - MOUNT: Mounts the QEMU disc to allow you transfer files between your computer and Linux.
 - UNMOUNT: Unmounts the QEMU disc.

## Configuring
You can configure easyTOS by editing the global constants in the Python file.
You can change the amount of storage and ram to give the VM. You can also edit
the mount point.
