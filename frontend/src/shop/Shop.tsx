import React from "react";
import SellButton from "./SellButton";

interface ShopProps {
  onSellItem: () => Promise<void> | void;
  onSellBook: () => Promise<void> | void;
}

/**
 * Minimal shop UI providing buttons to sell items or books. The parent is
 * responsible for performing API calls once the user confirms the action.
 */
const Shop: React.FC<ShopProps> = ({ onSellItem, onSellBook }) => {
  return (
    <div>
      <SellButton onConfirm={onSellItem} label="Sell Item" />
      <SellButton onConfirm={onSellBook} label="Sell Book" />
    </div>
  );
};

export default Shop;
