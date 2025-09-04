import React, { useEffect, useState } from 'react';

interface Listing {
  id: number;
  title: string;
  description: string;
  current_price_cents: number;
}

interface Props {
  reloadKey: number;
}

const ListingList: React.FC<Props> = ({ reloadKey }) => {
  const [listings, setListings] = useState<Listing[]>([]);
  const [bids, setBids] = useState<Record<number, number>>({});

  const load = () => {
    fetch('/marketplace/listings')
      .then((res) => res.json())
      .then(setListings);
  };

  useEffect(() => {
    load();
  }, [reloadKey]);

  const placeBid = async (id: number) => {
    const amount = bids[id];
    if (!amount) return;
    await fetch(`/marketplace/listings/${id}/bid`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: amount }),
    });
    setBids((prev) => ({ ...prev, [id]: 0 }));
    load();
  };

  const purchase = async (id: number) => {
    await fetch(`/marketplace/listings/${id}/purchase`, { method: 'POST' });
    load();
  };

  return (
    <div>
      <h3 className="font-semibold">Listings</h3>
      <ul className="space-y-2">
        {listings.map((l) => (
          <li key={l.id} className="border p-2">
            <div className="font-bold">{l.title}</div>
            <div className="text-sm">{l.description}</div>
            <div>Current: {l.current_price_cents}¢</div>
            <div className="flex space-x-2 mt-1">
              <input
                type="number"
                className="border px-1 w-24"
                value={bids[l.id] || ''}
                onChange={(e) =>
                  setBids({ ...bids, [l.id]: Number(e.target.value) })
                }
                placeholder="Bid (¢)"
              />
              <button
                className="text-blue-500"
                onClick={() => placeBid(l.id)}
              >
                Bid
              </button>
              <button
                className="text-green-600"
                onClick={() => purchase(l.id)}
              >
                Buy
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListingList;
