import React, { useState } from 'react';
import ShipmentList from './ShipmentList';

const ShippingPanel: React.FC = () => {
  const [source, setSource] = useState<number>(0);
  const [dest, setDest] = useState<number>(0);
  const [item, setItem] = useState<number>(0);
  const [qty, setQty] = useState<number>(1);
  const [refresh, setRefresh] = useState(0);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/shipping/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_shop_id: source,
        dest_shop_id: dest,
        item_id: item,
        quantity: qty,
      }),
    });
    setSource(0);
    setDest(0);
    setItem(0);
    setQty(1);
    setRefresh((r) => r + 1);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="space-y-2">
        <input
          type="number"
          className="border px-1 w-full"
          placeholder="Source shop ID"
          value={source}
          onChange={(e) => setSource(Number(e.target.value))}
        />
        <input
          type="number"
          className="border px-1 w-full"
          placeholder="Destination shop ID"
          value={dest}
          onChange={(e) => setDest(Number(e.target.value))}
        />
        <input
          type="number"
          className="border px-1 w-full"
          placeholder="Item ID"
          value={item}
          onChange={(e) => setItem(Number(e.target.value))}
        />
        <input
          type="number"
          className="border px-1 w-full"
          placeholder="Quantity"
          value={qty}
          onChange={(e) => setQty(Number(e.target.value))}
        />
        <button type="submit" className="text-blue-500">
          Ship Item
        </button>
      </form>
      <ShipmentList refresh={refresh} />
    </div>
  );
};

export default ShippingPanel;
