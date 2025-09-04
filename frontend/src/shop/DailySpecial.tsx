import React, { useEffect, useState } from 'react';

interface Special {
  item: string;
  description: string;
}

const DailySpecial: React.FC = () => {
  const [special, setSpecial] = useState<Special | null>(null);

  useEffect(() => {
    fetch('/shop/daily-special')
      .then((r) => r.json())
      .then((data) => setSpecial(data));
  }, []);

  if (!special) return null;

  return (
    <div className="p-2 bg-yellow-100">
      <strong>{special.item}: </strong>
      <span>{special.description}</span>
    </div>
  );
};

export default DailySpecial;
