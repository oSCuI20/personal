#!/bin/bash

DEVICE=/dev/sda
ISO=/home/ebanderas/Descargas/debian-9.8.0-amd64-netinst.iso

umount ${DEVICE}*
parted ${DEVICE} --script mktable gpt
parted ${DEVICE} --script mkpart EFI fat16 1MiB 10MiB
parted ${DEVICE} --script mkpart live fat16 10MiB 3GiB
parted ${DEVICE} --script mkpart persistence ext4 3GiB 100%
parted ${DEVICE} --script set 1 msftdata on
parted ${DEVICE} --script set 2 legacy_boot on
parted ${DEVICE} --script set 2 msftdata on

mkfs.vfat -n EFI ${DEVICE}1
mkfs.vfat -n LIVE ${DEVICE}2
mkfs.ext4 -F -L persistence ${DEVICE}3

mkdir /tmp/usb-efi /tmp/usb-live /tmp/usb-persistence /tmp/live-iso
mount ${DEVICE}1 /tmp/usb-efi
mount ${DEVICE}2 /tmp/usb-live
mount ${DEVICE}3 /tmp/usb-persistence
mount -oro ${ISO} /tmp/live-iso

cp -ar /tmp/live-iso/* /tmp/usb-live

echo "/ union" > /tmp/usb-persistence/persistence.conf

grub-install --removable --target=x86_64-efi --boot-directory=/tmp/usb-live/boot/ --efi-directory=/tmp/usb-efi ${DEVICE}

dd bs=440 count=1 conv=notrunc if=/usr/lib/syslinux/mbr/gptmbr.bin of=${DEVICE}
syslinux --install ${DEVICE}2

cp -R /tmp/live-iso/isolinux /tmp/usb-live/syslinux
cp /tmp/live-iso/syslinux/isolinux.bin /tmp/usb-live/syslinux/syslinux.bin
cp /tmp/live-iso/syslinux/isolinux.cfg /tmp/usb-live/syslinux/syslinux.cfg

sed --in-place 's#isolinux/splash#syslinux/splash#' /tmp/usb-live/boot/grub/grub.cfg
sed --in-place '0,/boot=live/{s/\(boot=live .*\)$/\1 persistence/}' \
    /tmp/usb-live/boot/grub/grub.cfg /tmp/usb-live/syslinux/menu.cfg
sed --in-place '0,/boot=live/{s/\(boot=live .*\)$/\1 keyboard-layouts=de locales=en_US.UTF-8,de_DE.UTF-8/}' \
    /tmp/usb-live/boot/grub/grub.cfg /tmp/usb-live/syslinux/menu.cfg

umount /tmp/usb-efi /tmp/usb-live /tmp/usb-persistence /tmp/live-iso
sync
rmdir /tmp/usb-efi /tmp/usb-live /tmp/usb-persistence /tmp/live-iso
