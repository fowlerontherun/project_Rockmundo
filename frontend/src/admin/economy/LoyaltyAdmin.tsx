import React, { useEffect, useState } from 'react';

interface Tier {
  name: string;
  threshold: number;
  discount: number;
}

const LoyaltyAdmin: React.FC = () => {
  const [tiers, setTiers] = useState<Tier[]>([]);

  const load = () => {
    fetch('/admin/economy/loyalty/tiers')
      .then((res) => res.json())
      .then(setTiers);
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const name = (form.elements.namedItem('name') as HTMLInputElement).value;
    const threshold = Number(
      (form.elements.namedItem('threshold') as HTMLInputElement).value,
    );
    const discount = Number(
      (form.elements.namedItem('discount') as HTMLInputElement).value,
    );
    await fetch('/admin/economy/loyalty/tiers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, threshold, discount }),
    });
    form.reset();
    load();
  };

  const handleDelete = async (name: string) => {
    await fetch(`/admin/economy/loyalty/tiers/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
    load();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Loyalty Tiers</h2>
      <ul className="mb-4">
        {tiers.map((t) => (
          <li key={t.name} className="mb-2">
            {t.name} - {t.threshold} pts - {t.discount}%
            <button
              className="ml-2 text-red-600"
              onClick={() => handleDelete(t.name)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={handleAdd} className="space-x-2">
        <input
          name="name"
          placeholder="Name"
          className="border px-2"
          required
        />
        <input
          name="threshold"
          type="number"
          placeholder="Points"
          className="border px-2"
          required
        />
        <input
          name="discount"
          type="number"
          step="0.1"
          placeholder="Discount %"
          className="border px-2"
          required
        />
        <button type="submit" className="bg-blue-500 text-white px-3 py-1">
          Add / Update
        </button>
      </form>
    </div>
  );
};

export default LoyaltyAdmin;
