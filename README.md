# build-at-extension

This omniverse extension listens on a user-provided MQTT topic and forwards the data received to an internal omniverse bus, which can then be used by Action Graphs.  

# Adding this extension

In Omniverse, go to the Extensions window -> hamburger menu -> Settings.
Under "Extension Search Paths", add this field: `git://github.com/purdue-ie-labs/build-at-extension.git?branch=main&dir=exts`. This should discover the extension.

# Contributing
To enable intellisense and setup the development environment, do the following:
1. `git clone https://github.com/Purdue-IE-Labs/build-at-extension.git && cd build-at-extension`
2. `python -m venv venv` to create a virtual environment to house your python dependencies (outside of omniverse-specific dependencies)
    - worry about versioning here
3. `./venv/Scripts/activate`
    - this command will be different if you are not on Windows
4. `pip install -r requirements.txt`
5. We need to change the Python version that VSCode is using and point it to the virtual environment that we 
just created. Open any Python file in the project (for example, `extension.py`) and click the version on the 
far right of the bottom toolbar of VSCode. When the select interpreter dialogue box opens, select "Enter 
interpreter path..." and find the python executable found at `venv/Scripts/python`. This may require reloading your VSCode window.
5. In order to allow the VSCode Python extensions to find the omniverse dependencies, we need to modify the path variable. Navigate to Pylance Extension (install it if you haven't). Click the gear icon and then settings. Type `@id:python.analysis.extraPaths @ext:ms-python.vscode-pylance extraPath` in the search bar and add the following:
    - `./build-at-extension/app/extscache/omni.ui-2.25.22+10a4b5c0.wx64.r.cp310`
    - `./build-at-extension/app/kit/kernel/py`