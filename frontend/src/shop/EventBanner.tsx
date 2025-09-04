import React, { useEffect, useState } from 'react';

interface ShopEvent {
  id: number;
  banner: string;
  end_time: string;
}

const ShopEventBanner: React.FC = () => {
  const [event, setEvent] = useState<ShopEvent | null>(null);
  const [remaining, setRemaining] = useState('');

  useEffect(() => {
    fetch('/shop/event')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.banner) setEvent(data);
      });
  }, []);

  useEffect(() => {
    if (!event) return;
    const timer = setInterval(() => {
      const diff = new Date(event.end_time).getTime() - Date.now();
      if (diff <= 0) {
        setRemaining('0s');
        clearInterval(timer);
      } else {
        const sec = Math.floor(diff / 1000) % 60;
        const min = Math.floor(diff / 60000) % 60;
        const hr = Math.floor(diff / 3600000);
        setRemaining(`${hr}h ${min}m ${sec}s`);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [event]);

  if (!event) return null;

  return (
    <div className="p-2 bg-blue-200 text-center">
      <strong>{event.banner}</strong>
      <span className="ml-2">Ends in {remaining}</span>
    </div>
  );
};

export default ShopEventBanner;
