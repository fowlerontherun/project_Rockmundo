import React, { useEffect, useState } from 'react';

interface PluginInfo {
  name: string;
  version: string;
  author?: string | null;
  enabled: boolean;
}

const PluginManager: React.FC = () => {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);

  const load = async () => {
    try {
      const res = await fetch('/admin/modding/plugins');
      const data = await res.json();
      setPlugins(data);
    } catch {
      // swallow errors for now
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggle = async (name: string, enabled: boolean) => {
    const action = enabled ? 'disable' : 'enable';
    await fetch(`/admin/modding/plugins/${name}/${action}`, { method: 'POST' });
    load();
  };

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-4">Plugins</h2>
      <ul>
        {plugins.map((p) => (
          <li key={p.name} className="flex items-center justify-between mb-2">
            <span>
              {p.name} v{p.version}
              {p.author ? ` by ${p.author}` : ''}
            </span>
            <button
              className="px-2 py-1 bg-blue-500 text-white rounded"
              onClick={() => toggle(p.name, p.enabled)}
            >
              {p.enabled ? 'Disable' : 'Enable'}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PluginManager;
