import React, { useEffect, useState } from 'react';

interface Tier {
  name: string;
  monthly_fee: number;
  discount: number;
}

interface Membership {
  tier: string;
  renew_at: string;
}

const Membership: React.FC = () => {
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [membership, setMembership] = useState<Membership | null>(null);
  const [selected, setSelected] = useState('');

  const load = () => {
    fetch('/membership/tiers')
      .then((r) => r.json())
      .then((data) => setTiers(data));
    fetch('/membership/me')
      .then((r) => r.json())
      .then((data) => {
        setMembership(Object.keys(data).length ? data : null);
      });
  };

  useEffect(() => {
    load();
  }, []);

  const join = () => {
    if (!selected) return;
    fetch('/membership/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tier: selected }),
    }).then(() => load());
  };

  const renew = () => {
    fetch('/membership/renew', { method: 'POST' }).then(() => load());
  };

  const cancel = () => {
    fetch('/membership/cancel', { method: 'POST' }).then(() => setMembership(null));
  };

  return (
    <div>
      <h3>Membership</h3>
      {membership ? (
        <div>
          <p>
            Current: {membership.tier} (renews {new Date(membership.renew_at).toLocaleDateString()})
          </p>
          <button onClick={renew}>Renew</button>
          <button onClick={cancel} className="ml-2">
            Cancel
          </button>
        </div>
      ) : (
        <div>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="">Select tier</option>
            {tiers.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name} - {t.monthly_fee}¢ ({t.discount}% off)
              </option>
            ))}
          </select>
          <button onClick={join} disabled={!selected} className="ml-2">
            Join
          </button>
        </div>
      )}
    </div>
  );
};

export default Membership;
