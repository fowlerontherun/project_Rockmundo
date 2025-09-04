import React, { useEffect, useState } from 'react';

interface Shop {
  id: number;
  city: string;
  name: string;
}

interface Item {
  item_id: number;
  quantity: number;
  price_cents: number;
}

interface Book {
  book_id: number;
  quantity: number;
  price_cents: number;
}

const PlayerShopAdmin: React.FC = () => {
  const [shops, setShops] = useState<Shop[]>([]);
  const [items, setItems] = useState<Record<number, Item[]>>({});
  const [books, setBooks] = useState<Record<number, Book[]>>({});
  const [revenue, setRevenue] = useState<Record<number, number>>({});

  const loadInventory = (shopId: number) => {
    Promise.all([
      fetch(`/admin/economy/player-shops/${shopId}/items`).then((r) => r.json()),
      fetch(`/admin/economy/player-shops/${shopId}/books`).then((r) => r.json()),
      fetch(`/admin/economy/player-shops/${shopId}/revenue`).then((r) => r.json()),
    ]).then(([itemData, bookData, revData]) => {
      setItems((prev) => ({ ...prev, [shopId]: itemData }));
      setBooks((prev) => ({ ...prev, [shopId]: bookData }));
      setRevenue((prev) => ({ ...prev, [shopId]: revData.revenue_cents }));
    });
  };

  const loadShops = () => {
    fetch('/admin/economy/player-shops')
      .then((res) => res.json())
      .then((data) => {
        setShops(data);
        data.forEach((s: Shop) => loadInventory(s.id));
      });
  };

  useEffect(() => {
    loadShops();
  }, []);

  const handleUpdateItem = async (
    shopId: number,
    itemId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/player-shops/${shopId}/items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price_cents: price }),
    });
    loadInventory(shopId);
  };

  const handleUpdateBook = async (
    shopId: number,
    bookId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/player-shops/${shopId}/books/${bookId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price_cents: price }),
    });
    loadInventory(shopId);
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">My Shops</h2>
      {shops.map((shop) => (
        <div key={shop.id} className="border p-4 mb-4">
          <h3 className="font-semibold">
            {shop.name} ({shop.city})
          </h3>
          <div className="mb-2">
            Revenue: ${(revenue[shop.id] || 0) / 100}
          </div>
          <div className="mb-4">
            <h4 className="font-medium">Items</h4>
            {items[shop.id]?.map((item) => (
              <form
                key={item.item_id}
                onSubmit={(e) => handleUpdateItem(shop.id, item.item_id, e)}
                className="mb-2 flex gap-2"
              >
                <span>
                  Item {item.item_id} qty {item.quantity}
                </span>
                <input
                  name="priceCents"
                  defaultValue={item.price_cents}
                  className="border px-1 w-24"
                />
                <button type="submit" className="bg-blue-500 text-white px-2">
                  Save
                </button>
              </form>
            ))}
          </div>
          <div>
            <h4 className="font-medium">Books</h4>
            {books[shop.id]?.map((book) => (
              <form
                key={book.book_id}
                onSubmit={(e) => handleUpdateBook(shop.id, book.book_id, e)}
                className="mb-2 flex gap-2"
              >
                <span>
                  Book {book.book_id} qty {book.quantity}
                </span>
                <input
                  name="priceCents"
                  defaultValue={book.price_cents}
                  className="border px-1 w-24"
                />
                <button type="submit" className="bg-blue-500 text-white px-2">
                  Save
                </button>
              </form>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PlayerShopAdmin;
