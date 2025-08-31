import React, { useState } from 'react';

interface PreviewResponse {
  lines: string[];
}

const DialogueEditor: React.FC = () => {
  const [npcId, setNpcId] = useState('');
  const [dialogue, setDialogue] = useState('{\n  "root": "start",\n  "nodes": {}\n}');
  const [choices, setChoices] = useState('');
  const [preview, setPreview] = useState<string[]>([]);

  const save = async () => {
    await fetch(`/admin/npcs/dialogue/${npcId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: dialogue,
    });
  };

  const runPreview = async () => {
    const res = await fetch(`/admin/npcs/dialogue/${npcId}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        choices: choices
          .split(',')
          .map((c) => parseInt(c.trim(), 10))
          .filter((n) => !isNaN(n)),
      }),
    });
    const data: PreviewResponse = await res.json();
    setPreview(data.lines);
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">NPC Dialogue Editor</h2>
      <div className="mb-2">
        <label className="mr-2">NPC ID:</label>
        <input
          className="border p-1"
          value={npcId}
          onChange={(e) => setNpcId(e.target.value)}
        />
      </div>
      <textarea
        className="w-full border p-2 mb-2 font-mono"
        rows={12}
        value={dialogue}
        onChange={(e) => setDialogue(e.target.value)}
      />
      <div className="mb-4 space-x-2">
        <button className="bg-blue-500 text-white px-3 py-1" onClick={save}>
          Save
        </button>
      </div>
      <div className="mb-2">
        <label className="mr-2">Preview choices (comma separated):</label>
        <input
          className="border p-1"
          value={choices}
          onChange={(e) => setChoices(e.target.value)}
        />
        <button
          className="bg-green-600 text-white px-2 py-1 ml-2"
          onClick={runPreview}
        >
          Preview
        </button>
      </div>
      <ul className="list-disc pl-5">
        {preview.map((line, idx) => (
          <li key={idx}>{line}</li>
        ))}
      </ul>
    </div>
  );
};

export default DialogueEditor;
