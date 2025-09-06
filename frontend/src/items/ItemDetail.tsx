import React, { useState } from 'react';

interface Props {
  id: number;
  name: string;
  durability: number;
  ownerId: number;
}

const ItemDetail: React.FC<Props> = ({ id, name, durability, ownerId }) => {
  const [dur, setDur] = useState(durability);

  const handleRepair = async () => {
    const res = await fetch(`/shop/items/${id}/repair`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ owner_user_id: ownerId }),
    });
    if (res.ok) {
      const data = await res.json();
      setDur(data.new_durability ?? 100);
    }
  };

  return (
    <div className="p-2 border rounded">
      <h3 className="font-bold">{name}</h3>
      <div className="h-2 bg-gray-200 mt-2">
        <div
          role="progressbar"
          className="h-2 bg-green-500"
          style={{ width: `${dur}%` }}
        />
      </div>
      <button
        className="mt-2 bg-blue-500 text-white px-2 py-1 rounded"
        onClick={handleRepair}
      >
        Repair
      </button>
    </div>
  );
};

export default ItemDetail;
