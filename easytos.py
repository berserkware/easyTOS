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
CPU_COUNT = 2
MOUNT_POINT = '/mnt/templeos'
ISO_SOURCE = 'https://templeos.org/Downloads/TempleOS.ISO'

def get_iso():
    """Downloads the TempleOS ISO."""
    print("Downloading TempleOS ISO...")
    response = requests.get(ISO_SOURCE)
    with open('/var/lib/easytos/TempleOS.ISO', mode='wb') as file:
        file.write(response.content)
    print("ISO written to /var/lib/easytos.")


class SudoNotice(tk.Frame):
    """The notice to tell the user they need to run as sudo."""
    
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.message = ttk.Label(
            self,
            text='easyTOS needs superuser permissions to run.',
        )
        self.message.pack()
    
        self.button = ttk.Button(
            self,
            text='Ok',
            command=args[0].destroy,
            width=40,
        )
        self.button.pack()


class CreateVM(tk.Toplevel):
    """A window for creating a VM."""
    
    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)

        self.wm_title("Create VM")
        self.wm_resizable(False, False)

        self.message = ttk.Label(
            self,
            text='Create VM',
            font=('Helvetica', 15),
        )
        self.message.pack(pady=5)
        
        self.install_button = ttk.Button(
            self,
            text='Create',
            command=self.do_install,
            width=30,
        )
        self.install_button.pack()
        

    def do_install(self):
        """Gets the TempleOS ISO, creates the QEMU Image, and runs it with the CD installed."""
        if not os.path.exists('/var/lib/easytos/TempleOS.ISO'):
            get_iso()

        if not os.path.exists('/var/lib/easytos/templeos.qcow2'):
            print("Creating QEMU img...")
            os.system(f'sudo qemu-img create /var/lib/easytos/templeos.qcow2 {VM_STORAGE}')
            print("Done.")

        print("Initial TempleOS boot...")
        os.system(
            f'sudo qemu-system-x86_64 -boot d -cdrom /var/lib/easytos/TempleOS.ISO -m {VM_MEMORY} -smp {CPU_COUNT} -drive file=/var/lib/easytos/templeos.qcow2,format=raw'
        )

        self.master.exit_button.pack_forget()
        self.master.run_button.pack()
        self.master.mount_button.pack()
        self.master.exit_button.pack()
        
    
class MainMenu(tk.Frame):
    """The main menu."""
    
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.message = ttk.Label(
            self,
            text='easyTOS!',
            font=('Helvetica', 30),
        )
        self.message.pack(pady=8)

        self.run_button = ttk.Button(
            self,
            text='RUN',
            command=self.do_run,
            width=30,
        )
        if os.path.exists('/var/lib/easytos/templeos.qcow2'):
            self.run_button.pack()
            
        self.install_button = ttk.Button(
            self,
            text='INSTALL/REINSTALL',
            command=lambda: CreateVM(self),
            width=30,
        )
        self.install_button.pack()

        self.mount_button = ttk.Button(
            self,
            text='MOUNT',
            command=self.do_mount,
            width=30,
        )
        if(os.path.exists('/var/lib/easytos/templeos.qcow2') and
           not os.path.exists(MOUNT_POINT)):
            self.mount_button.pack()

        self.unmount_button = ttk.Button(
            self,
            text='UNMOUNT',
            command=self.do_unmount,
            width=30,
        )
        if os.path.exists(MOUNT_POINT):
            self.unmount_button.pack()

        self.exit_button = ttk.Button(
            self,
            text='EXIT',
            command=args[0].destroy,
            width=30,
        )
        self.exit_button.pack()

    def do_run(self):
        """Runs TempleOS."""
        print("Starting TempleOS...")
        subprocess.Popen(
            f'sudo qemu-system-x86_64 -m {VM_MEMORY} -smp {CPU_COUNT} -drive file=/var/lib/easytos/templeos.qcow2,format=raw',
            shell=True,
        )

    def do_mount(self):
        """Mounts the QEMU disc."""
        if not os.path.exists(MOUNT_POINT):
            os.mkdir(MOUNT_POINT)

        print("Mounting drive...")
        os.system('modprobe nbd max_part=8')
        os.system('qemu-nbd --connect=/dev/nbd0 /var/lib/easytos/templeos.qcow2')
        os.system('mount /dev/nbd0p1 /mnt/templeos')
        print("Mounted at /mnt/templeos.")
        
        self.exit_button.pack_forget()
        self.unmount_button.pack()
        self.mount_button.pack_forget()
        self.exit_button.pack()
        
    def do_unmount(self):
        """Unmounts the QEMU disc."""
        print("Unmounting drive...")
        os.system(f'umount {MOUNT_POINT}')
        os.system('qemu-nbd --disconnect /dev/nbd0')
        os.system('rmmod nbd')
        os.rmdir(MOUNT_POINT)
        print("Done.")

        self.exit_button.pack_forget()
        self.unmount_button.pack_forget()
        self.mount_button.pack()
        self.exit_button.pack()

    
if __name__ == '__main__':
    root = tk.Tk()
    root.title('easyTOS');
    root.resizable(False, False)

    if os.geteuid() != 0:
        print("Superuser Privileges are needed to run easyTOS!")
        sudo_notice = SudoNotice(root)
        sudo_notice.pack(side="top", fill="both", expand=True)
    else:
        if not os.path.isdir('/var/lib/easytos'):
            os.mkdir('/var/lib/easytos')
            
        main_menu = MainMenu(root)
        main_menu.pack(side="top", fill="both", expand=True)

    root.mainloop()
