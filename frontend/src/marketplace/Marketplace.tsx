import React, { useState } from 'react';
import ListingList from './ListingList';
import NewListingForm from './NewListingForm';

const Marketplace: React.FC = () => {
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);
  return (
    <div className="p-4 space-y-4">
      <NewListingForm onCreated={reload} />
      <ListingList reloadKey={reloadKey} />
    </div>
  );
};

export default Marketplace;
