import React, { useState } from 'react';
import SellButton from './SellButton';
import HaggleDialog from './HaggleDialog';

interface Props {
  id: number;
  name: string;
  price_cents: number;
  trend: 'up' | 'down' | 'stable';
  onSell: (id: number) => void;
}

const symbolMap = { up: '▲', down: '▼', stable: '→' };

const ShopItem: React.FC<Props> = ({ id, name, price_cents, trend, onSell }) => {
  const [showHaggle, setShowHaggle] = useState(false);

  return (
    <div className="flex flex-col border-b py-1">
      <div className="flex justify-between items-center">
        <span>
          {name} - {price_cents}¢ <span>{symbolMap[trend]}</span>
        </span>
        <div className="space-x-2">
          <button
            className="px-2 py-1 bg-yellow-200"
            onClick={() => setShowHaggle((s) => !s)}
          >
            Haggle
          </button>
          <SellButton onConfirm={() => onSell(id)} />
        </div>
      </div>
      {showHaggle && <HaggleDialog itemId={id} basePrice={price_cents} />}
    </div>
  );
};

export default ShopItem;
