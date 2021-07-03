# timonel-py
A timonel bootloader control program for python

Based on timonel boot loader at https://www.github.com/casanovg/timonel and related repositories. Start there if you want to learn about the boot loader itself.

Use at your own risk! This is pre-alpha quality. Seriously, I take no liability. Have fun, but but don't come crying to me if your microcontroller explodes or the dog divorces you. 

Having said that, I am interested in bug reports and suggestions for improvement. I'm learning all the time, both python and timonel, so there's room for improvement.

## Read this now and be disappointed early!
- Not all functions are implemented. (Pre-Alpha!) With the exception of EEPROM writing, there are no commands to load anything, yet.
- All communication to the device checks that the first byte is a correct ACK, and where appropriate calculates checkums, but does not retry on failure.
- There are no delays for certain actions that might need them.
- Assumptions about buffer sizes are optimistic.
- I am tracking V1.6 as this has a more consistent little-endian structure throughout.

## How do you attach a PC to I2C?

That's up to you. If you have a device that is compatible with the python smbus2 library you should be OK. I use a PC running under a Ubuntu derivative that has kernel drivers for /dev/i2c-x. 

The I2C tiny USB library (https://github.com/harbaum/I2C-Tiny-USB) allows you to create your own adapter. The easiest option I've found is to flash the Digispark version, just plug it into a USB port, and off you go.

It is whispered by the elves that Raspberry PI computers have an I2C interface that works out of the box. To be honest with you, I have an old RPi version 1 and I couldn't get it work reliably, but that could be just me. If you can get it work by flashing Timonel on an appropriate target (ATTiny85) and connecting it up, send me some notes and I'll document it here.

## I want feature X!!!! I want it now!!!

I'm truly, deeply impressed that you think I can help. I'm doing this in my spare time and I simply can't guarantee anything. But I've put the code under a two-clause BSD licence so you're absolutely OK to copy and do what you want with is, so long as you credit me for the initial work. Drop me an email, maybe. Buy me a coffee. Whatever.
