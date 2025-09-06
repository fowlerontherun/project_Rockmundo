import React, { useEffect, useState } from 'react';

interface Props {
  reloadKey: number;
}

interface AccountInfo {
  balance_cents: number;
  savings_cents: number;
}

const AccountView: React.FC<Props> = ({ reloadKey }) => {
  const [info, setInfo] = useState<AccountInfo>({ balance_cents: 0, savings_cents: 0 });
  const [depositAmt, setDepositAmt] = useState(0);
  const [withdrawAmt, setWithdrawAmt] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/bank/account');
        if (res.ok) {
          const data = await res.json();
          setInfo(data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, [reloadKey]);

  const deposit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/bank/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: depositAmt }),
    });
    setDepositAmt(0);
  };

  const withdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/bank/withdraw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: withdrawAmt }),
    });
    setWithdrawAmt(0);
  };

  return (
    <div className="space-y-2">
      <div>Balance: {info.balance_cents}¢</div>
      <div>Savings: {info.savings_cents}¢</div>
      <form onSubmit={deposit} className="space-x-2">
        <input
          type="number"
          value={depositAmt}
          onChange={(e) => setDepositAmt(Number(e.target.value))}
          className="border px-1"
        />
        <button type="submit" className="text-blue-500">
          Deposit
        </button>
      </form>
      <form onSubmit={withdraw} className="space-x-2">
        <input
          type="number"
          value={withdrawAmt}
          onChange={(e) => setWithdrawAmt(Number(e.target.value))}
          className="border px-1"
        />
        <button type="submit" className="text-blue-500">
          Withdraw
        </button>
      </form>
    </div>
  );
};

export default AccountView;
