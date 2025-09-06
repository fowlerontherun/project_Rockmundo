import React, { useEffect, useState } from 'react';

interface DialogueResponse {
  lines: string[];
  options: string[];
}

const ShopDialogue: React.FC = () => {
  const [choices, setChoices] = useState<number[]>([]);
  const [dialogue, setDialogue] = useState<DialogueResponse>({ lines: [], options: [] });

  useEffect(() => {
    const query = choices.join(',');
    fetch(`/shop/npc/dialogue?choices=${query}`)
      .then((r) => r.json())
      .then((data) => setDialogue(data));
  }, [choices]);

  return (
    <div className="space-y-2">
      {dialogue.lines.map((l, i) => (
        <p key={i}>{l}</p>
      ))}
      <div className="space-x-2">
        {dialogue.options.map((opt, idx) => (
          <button
            key={idx}
            className="px-2 py-1 bg-blue-200"
            onClick={() => setChoices([...choices, idx])}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ShopDialogue;
