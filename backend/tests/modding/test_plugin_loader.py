import sys

from backend.modding.loader import PluginLoader
from backend.modding.interfaces import PluginMeta


def test_plugin_registration(tmp_path, monkeypatch):
    plugin_code = (
        "from backend.modding.interfaces import PluginMeta\n"
        "class Sample:\n"
        "    meta = PluginMeta(name='sample', version='1.0', author='tester')\n"
        "    activated = False\n"
        "    def activate(self):\n"
        "        self.activated = True\n"
        "plugin = Sample()\n"
    )
    mod = tmp_path / "myplugin.py"
    mod.write_text(plugin_code)
    monkeypatch.syspath_prepend(str(tmp_path))

    loader = PluginLoader()
    loader.load_from_modules(["myplugin"])
    assert "sample" in loader.plugins
    assert loader.plugins["sample"].activated is True
