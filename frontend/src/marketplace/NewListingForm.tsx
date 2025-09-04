import React, { useState } from 'react';

interface Props {
  onCreated: () => void;
}

const NewListingForm: React.FC<Props> = ({ onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState<number>(0);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/marketplace/listings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description,
        starting_price_cents: price,
      }),
    });
    setTitle('');
    setDescription('');
    setPrice(0);
    onCreated();
  };

  return (
    <form onSubmit={submit} className="space-y-2">
      <input
        className="border px-1 w-full"
        placeholder="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        className="border px-1 w-full"
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <input
        className="border px-1 w-full"
        type="number"
        placeholder="Starting price (¢)"
        value={price}
        onChange={(e) => setPrice(Number(e.target.value))}
      />
      <button type="submit" className="text-blue-500">
        List Item
      </button>
    </form>
  );
};

export default NewListingForm;
