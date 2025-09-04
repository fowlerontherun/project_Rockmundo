import React, { useState } from 'react';

interface Props {
  itemId: number;
  basePrice: number;
}

interface HaggleResult {
  counteroffer_cents?: number;
  accepted?: boolean;
  lines?: string[];
}

const HaggleDialog: React.FC<Props> = ({ itemId, basePrice }) => {
  const [offer, setOffer] = useState<number>(basePrice);
  const [skill, setSkill] = useState<number>(0);
  const [reputation, setReputation] = useState<number>(0);
  const [result, setResult] = useState<HaggleResult>({});

  const submit = () => {
    fetch(`/shop/items/${itemId}/haggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offer_cents: offer, skill, reputation }),
    })
      .then((r) => r.json())
      .then((data) => setResult(data));
  };

  return (
    <div className="space-y-2 border p-2 mt-2">
      <div>
        <label>
          Offer (¢):
          <input
            type="number"
            value={offer}
            onChange={(e) => setOffer(parseInt(e.target.value, 10))}
            className="ml-1 w-16 border"
          />
        </label>
      </div>
      <div className="space-x-2">
        <label>
          Skill:
          <input
            type="number"
            value={skill}
            onChange={(e) => setSkill(parseInt(e.target.value, 10))}
            className="ml-1 w-12 border"
          />
        </label>
        <label>
          Reputation:
          <input
            type="number"
            value={reputation}
            onChange={(e) => setReputation(parseInt(e.target.value, 10))}
            className="ml-1 w-12 border"
          />
        </label>
      </div>
      <button className="px-2 py-1 bg-green-200" onClick={submit}>
        Haggle
      </button>
      {result.counteroffer_cents !== undefined && (
        <p>
          Counteroffer: {result.counteroffer_cents}¢{' '}
          {result.accepted ? '- Deal!' : ''}
        </p>
      )}
      {result.lines && result.lines.map((l, i) => <p key={i}>{l}</p>)}
    </div>
  );
};

export default HaggleDialog;
