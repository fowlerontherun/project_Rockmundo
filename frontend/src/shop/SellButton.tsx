import React from 'react';

interface Props {
  onConfirm: () => void;
  label?: string;
}

const SellButton: React.FC<Props> = ({ onConfirm, label = 'Sell' }) => {
  const handleClick = () => {
    if (window.confirm('Are you sure you want to sell this item?')) {
      onConfirm();
    }
  };

  return (
    <button className="text-red-600" onClick={handleClick}>
      {label}
    </button>
  );
};

export default SellButton;
