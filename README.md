# Generate set up.

## Set up USB rules

You want to :
- rename the device useing a Symbolic link (SYMLINK)
- Change mode to 666 to allow read/write
- Set USB latency to 1ms. ATTR hierarchy can be seen by running:

1 -First run the following to get device specifications:
```console
udevadm info /dev/ttyUSBx
```

for elaborate info/to get latency timer value and hierarchy: udevadm info -a -n /dev/ttyUSBx


2 -create a file 99-revo-usb.rules in /etc/udev/rules.d with the following rules
```bash
ACTION=="add", SUBSYSTEM=="tty",ENV{ID_USB_INTERFACE_NUM}=="00", ENV{ID_SERIAL_SHORT}=="FT5CZ079", SYMLINK+="COM3", MODE="0666", ATTR{device/latency_timer}="1"

ACTION=="add", SUBSYSTEM=="tty",ENV{ID_USB_INTERFACE_NUM}=="01", ENV{ID_SERIAL_SHORT}=="FT5CZ079", SYMLINK+="COM4", MODE="0666", ATTR{device/latency_timer}="1"
```
For raspberry PI remove the ACTION=="add"

3- trigger new rules:

sudo udevadm trigger









