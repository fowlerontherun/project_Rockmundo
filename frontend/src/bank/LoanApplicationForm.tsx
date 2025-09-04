import React, { useState } from 'react';

interface Props {
  onSubmitted: () => void;
}

const LoanApplicationForm: React.FC<Props> = ({ onSubmitted }) => {
  const [amount, setAmount] = useState(0);
  const [rate, setRate] = useState(0.05);
  const [term, setTerm] = useState(30);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/bank/loan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        principal_cents: amount,
        interest_rate: rate,
        term_days: term,
      }),
    });
    setAmount(0);
    onSubmitted();
  };

  return (
    <form onSubmit={submit} className="space-y-2">
      <input
        type="number"
        className="border px-1 w-full"
        placeholder="Loan amount (¢)"
        value={amount}
        onChange={(e) => setAmount(Number(e.target.value))}
      />
      <input
        type="number"
        className="border px-1 w-full"
        step="0.01"
        placeholder="Interest rate"
        value={rate}
        onChange={(e) => setRate(Number(e.target.value))}
      />
      <input
        type="number"
        className="border px-1 w-full"
        placeholder="Term (days)"
        value={term}
        onChange={(e) => setTerm(Number(e.target.value))}
      />
      <button type="submit" className="text-blue-500">
        Apply for Loan
      </button>
    </form>
  );
};

export default LoanApplicationForm;
