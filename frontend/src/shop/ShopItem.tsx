import React from 'react';
import SellButton from './SellButton';

interface Props {
  id: number;
  name: string;
  onSell: (id: number) => void;
}

const ShopItem: React.FC<Props> = ({ id, name, onSell }) => (
  <div className="flex justify-between items-center border-b py-1">
    <span>{name}</span>
    <SellButton onConfirm={() => onSell(id)} />
  </div>
);

export default ShopItem;
