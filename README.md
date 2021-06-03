# timonel-py
A timonel bootloader control program for python

Based on timonel boot loader at https://www.github.com/casanovg/timonel and related repositories. Start there if you want to learn about the boot loader itself.

Use at your own risk! This is pre-alpha quality. Seriously, I take no liability. Have fun, but but don't come crying to me if your microcontroller explodes or the dog divorces you. 

Having said that, I am interested in bug reports and suggestions for improvement. I'm learning all the time, both python and timonel, so there's room for improvement.

Notably
- Not all functions are implemented. With the exception of EEPROM writing, there are no commands to load anything, yet.
- All communication to the device checks that the first byte is a correct ACK, and where appropriate calculates checkums, but does not retry on failure.
- There are no delays for certain actions that might need them.
- Assumptions about buffer sizes are optimistic
