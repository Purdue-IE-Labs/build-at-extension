# build-at-extension

This omniverse extension listens on a user-provided MQTT topic and forwards the data received to an internal omniverse bus, which can then be used by Action Graphs.  

# Adding this extension

In Omniverse, go to the Extensions window -> hamburger menu -> Settings.
Under "Extension Search Paths", add this field: `git://github.com/purdue-ie-labs/build-at-extension.git?branch=main&dir=.`. This should discover the extension.