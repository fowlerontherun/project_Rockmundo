import React from 'react';
import SellButton from './SellButton';

interface Props {
  id: number;
  name: string;
  price_cents: number;
  trend: 'up' | 'down' | 'stable';
  onSell: (id: number) => void;
}

const symbolMap = { up: '▲', down: '▼', stable: '→' };

const ShopItem: React.FC<Props> = ({ id, name, price_cents, trend, onSell }) => (
  <div className="flex justify-between items-center border-b py-1">
    <span>
      {name} - {price_cents}¢ <span>{symbolMap[trend]}</span>
    </span>
    <SellButton onConfirm={() => onSell(id)} />
  </div>
);

export default ShopItem;
