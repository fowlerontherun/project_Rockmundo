import React, { useState } from "react";

interface SellButtonProps {
  onConfirm: () => Promise<void> | void;
  label?: string;
}

/**
 * Simple button used for selling items or books. Clicking the button asks the
 * user to confirm the action before triggering the supplied callback.
 */
const SellButton: React.FC<SellButtonProps> = ({ onConfirm, label }) => {
  const [confirm, setConfirm] = useState(false);

  if (confirm) {
    return (
      <span>
        <button onClick={() => onConfirm()}>Confirm</button>
        <button onClick={() => setConfirm(false)}>Cancel</button>
      </span>
    );
  }

  return (
    <button onClick={() => setConfirm(true)}>{label || "Sell"}</button>
  );
};

export default SellButton;
