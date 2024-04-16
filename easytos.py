#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk
import os
import sys
import requests
import subprocess

# Edit these to modify the program
VM_MEMORY = 4096
VM_STORAGE = '5G'
MOUNT_POINT = '/mnt/templeos'

def do_run():
    """Runs TempleOS."""
    os.system(f'sudo qemu-system-x86_64 -m {VM_MEMORY} -hda /var/lib/easytos/templeos.qcow2')

def do_install():
    """Gets the TempleOS ISO, creates the QEMU Image, and runs it with the CD installed."""
    if not os.path.exists('/var/lib/easytos/TempleOS.ISO'):
        response = requests.get('https://templeos.org/Downloads/TempleOS.ISO')
        with open('/var/lib/easytos/TempleOS.ISO', mode='wb') as file:
            file.write(response.content)

    if not os.path.exists('/var/lib/easytos/templeos.qcow2'):
        os.system(f'sudo qemu-img create /var/lib/easytos/templeos.qcow2 {VM_STORAGE}')

    os.system(f'sudo qemu-system-x86_64 -boot d -cdrom /var/lib/easytos/TempleOS.ISO -m {VM_MEMORY} -hda /var/lib/easytos/templeos.qcow2')

def do_mount():
    """Mounts the QEMU disc."""
    if not os.path.exists(MOUNT_POINT):
        os.mkdir(MOUNT_POINT)

    os.system('modprobe nbd max_part=8')
    os.system('qemu-nbd --connect=/dev/nbd0 /var/lib/easytos/templeos.qcow2')
    os.system('mount /dev/nbd0p1 /mnt/templeos')
        
def do_unmount():
    """Unmounts the QEMU disc."""
    os.system(f'umount {MOUNT_POINT}')
    os.system('qemu-nbd --disconnect /dev/nbd0')
    os.system('rmmod nbd')
    os.rmdir(MOUNT_POINT)
        
def do_main_window():
    """Runs the program."""
    root = tk.Tk()
    root.title('easyTOS');
    root.resizable(False, False)

    message = ttk.Label(
        root,
        text='easyTOS!',
        font=('Helvetica', 30),
    )
    message.pack()

    if os.path.exists('/var/lib/easytos/templeos.qcow2'):
        button = ttk.Button(
            root,
            text='RUN',
            command=do_run,
            width=30,
        )
        button.pack()

    button = ttk.Button(
        root,
        text='INSTALL/REINSTALL',
        command=do_install,
        width=30,
    )
    button.pack()

    if(os.path.exists('/var/lib/easytos/templeos.qcow2') and
       not os.path.exists(MOUNT_POINT)):
        button = ttk.Button(
            root,
            text='MOUNT',
            command=do_mount,
            width=30,
        )
        button.pack()

    if os.path.exists(MOUNT_POINT):
        button = ttk.Button(
            root,
            text='UNMOUNT',
            command=do_unmount,
            width=30,
        )
        button.pack()

    """
    Will try to fix later
    button = ttk.Button(
        root,
        text='CONFIGURE EASYTOS',
        command=lambda: os.system(f'xdg-open {__file__}'),
        width=30,
    )
    button.pack()
    """
    
    root.mainloop()

def need_sudo():
    """Runs a window containing a notice that the program needs sudo."""
    root = tk.Tk()
    root.title('easyTOS!');

    root.resizable(False, False)

    message = ttk.Label(
        root,
        text='easyTOS needs superuser permissions to run.',
    )
    message.pack()
    
    button = ttk.Button(
        root,
        text='Ok',
        command=root.destroy,
        width=40,
    )
    button.pack()

    root.mainloop()
    
if __name__ == '__main__':
    if os.geteuid() != 0:
        need_sudo()
        sys.exit()

    if not os.path.isdir('/var/lib/easytos'):
        os.mkdir('/var/lib/easytos')
    
    do_main_window()
