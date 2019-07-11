# this is trash, make generic
pyang --plugindir \
  "$VIRTUAL_ENV"/lib/python3.7/site-packages/pyangbind/plugin \
  -f pybind interfaces.yang > interfaces.py
