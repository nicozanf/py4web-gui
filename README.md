# py4web-gui

This is a simple tkinter gui interface for the py4web framework. It gives you the power to run and fully manage py4web's instances
using your mouse, without ever touching the command line that scares many users.

![Alt text](./screenshots/main.png?raw=true "Main window") 


It's quite simple, but:

 * it works on Windows, Linux and MacOS
 * it shows all the running py4web's instances with their details. You can launch their Dashboard or Homepage, view logs and even stop them
 * you can graphically launch the additional py4web instances (as specified on the py4web-gui.toml file, which is created at the first runtime)
 * you can create new instance definitions, change and delete them
 

You can look at instances' details and current logs:

![Alt text](./screenshots/details.png?raw=true "Main window") 

change its parameters (saved on disk):


![Alt text](./screenshots/edit.png?raw=true "Main window") 


and even ask for the Dashboard password if needed:


![Alt text](./screenshots/ask4pw.png?raw=true "Main window") 


Last but not least, if combined with the binary versions (see https://github.com/nicozanf/py4web-pyinstaller), it surely makes the experience of installing and
running py4web even much simpler and enjoyable.


## MANUAL INSTALLATION

Just copy the `py4web-gui.py` file in the main py4web folder and run it. If you're not using a recent version of the py4web program (since August 2024), you'll also
need the icon files present in this repository under docs/images. Add the requirements if needed (see down here)

## REQUIREMENTS

It needs the `psutil` and `tomlkit` module, as stated on `py4web-gui.requirements.txt`.

## ISSUES:

None known



Enjoy!



