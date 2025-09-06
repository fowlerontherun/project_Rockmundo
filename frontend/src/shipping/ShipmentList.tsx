import React, { useEffect, useState } from 'react';

interface Shipment {
  id: number;
  source_shop_id: number;
  dest_shop_id: number;
  item_id: number;
  quantity: number;
  fee_cents: number;
  status: string;
  arrival_time: string;
}

interface Props {
  refresh: number;
}

const ShipmentList: React.FC<Props> = ({ refresh }) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);

  useEffect(() => {
    const load = async () => {
      const res = await fetch('/shipping/shipments');
      const data = await res.json();
      setShipments(data);
    };
    load();
  }, [refresh]);

  return (
    <div>
      <h3 className="font-bold">Shipments</h3>
      <ul>
        {shipments.map((s) => (
          <li key={s.id} className="border-b py-1">
            #{s.id} item {s.item_id} x{s.quantity} from {s.source_shop_id} to {s.dest_shop_id} - {s.status} (fee {s.fee_cents}¢)
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ShipmentList;
