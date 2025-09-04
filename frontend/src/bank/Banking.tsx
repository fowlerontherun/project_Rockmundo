import React, { useState } from 'react';
import AccountView from './AccountView';
import LoanApplicationForm from './LoanApplicationForm';

const Banking: React.FC = () => {
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  return (
    <div className="p-4 space-y-4">
      <AccountView reloadKey={reloadKey} />
      <LoanApplicationForm onSubmitted={reload} />
    </div>
  );
};

export default Banking;
