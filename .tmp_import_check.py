import importlib
mods=['streamline_vpn.core.merger','streamline_vpn.web.api','streamline_vpn.settings','streamline_vpn.__main__']
for m in mods:
    print('Importing', m)
    importlib.import_module(m)
    print('OK:', m)
print('Done')
