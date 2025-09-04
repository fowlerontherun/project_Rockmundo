import React, { useEffect, useState } from 'react';
import SchemaForm from '../components/SchemaForm';

interface Shop {
  id: number;
  city: string;
  name: string;
}

interface Item {
  item_id: number;
  quantity: number;
  restock_interval?: number | null;
  restock_quantity?: number | null;
  price_cents: number;
}

interface Book {
  book_id: number;
  quantity: number;

  restock_interval?: number | null;
  restock_quantity?: number | null;

  price_cents: number;

}

interface BundleItem {
  item_id: number;
  quantity: number;
}

interface Bundle {
  id: number;
  name: string;
  price_cents: number;
  promo_starts?: string | null;
  promo_ends?: string | null;
  items: BundleItem[];
}

const CityShopsAdmin: React.FC = () => {
  const [shops, setShops] = useState<Shop[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [items, setItems] = useState<Record<number, Item[]>>({});
  const [books, setBooks] = useState<Record<number, Book[]>>({});
  const [bundles, setBundles] = useState<Record<number, Bundle[]>>({});

  const loadShops = () => {
    fetch('/admin/economy/city-shops')
      .then((res) => res.json())
      .then(setShops);
  };

  const loadInventory = (shopId: number) => {
    Promise.all([
      fetch(`/admin/economy/city-shops/${shopId}/items`).then((r) => r.json()),
      fetch(`/admin/economy/city-shops/${shopId}/books`).then((r) => r.json()),
      fetch(`/admin/economy/city-shops/${shopId}/bundles`).then((r) => r.json()),
    ]).then(([itemData, bookData, bundleData]) => {
      setItems((prev) => ({ ...prev, [shopId]: itemData }));
      setBooks((prev) => ({ ...prev, [shopId]: bookData }));
      setBundles((prev) => ({ ...prev, [shopId]: bundleData }));
    });
  };

  useEffect(() => {
    loadShops();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`/admin/economy/city-shops/${id}`, { method: 'DELETE' });
    setEditingId(null);
    loadShops();
  };

  const handleAddItem = async (
    shopId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const itemId = Number(
      (form.elements.namedItem('itemId') as HTMLInputElement).value,
    );
    const quantity = Number(
      (form.elements.namedItem('quantity') as HTMLInputElement).value,
    );
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/city-shops/${shopId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, quantity, price_cents: price }),
    });
    form.reset();
    loadInventory(shopId);
  };

  const handleUpdateItem = async (
    shopId: number,
    itemId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const quantity = Number(
      (form.elements.namedItem('quantity') as HTMLInputElement).value,
    );
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/city-shops/${shopId}/items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity, price_cents: price }),
    });
    loadInventory(shopId);
  };

  const handleRemoveItem = async (
    shopId: number,
    itemId: number,
    quantity: number,
  ) => {
    await fetch(
      `/admin/economy/city-shops/${shopId}/items/${itemId}?quantity=${quantity}`,
      { method: 'DELETE' },
    );
    loadInventory(shopId);
  };

  const handleAddBook = async (
    shopId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const bookId = Number(
      (form.elements.namedItem('bookId') as HTMLInputElement).value,
    );
    const quantity = Number(
      (form.elements.namedItem('quantity') as HTMLInputElement).value,
    );
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/city-shops/${shopId}/books`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ book_id: bookId, quantity, price_cents: price }),
    });
    form.reset();
    loadInventory(shopId);
  };

  const handleUpdateBook = async (
    shopId: number,
    bookId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const quantity = Number(
      (form.elements.namedItem('quantity') as HTMLInputElement).value,
    );
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    await fetch(`/admin/economy/city-shops/${shopId}/books/${bookId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity, price_cents: price }),
    });
    loadInventory(shopId);
  };

  const handleRemoveBook = async (
    shopId: number,
    bookId: number,
    quantity: number,
  ) => {
    await fetch(
      `/admin/economy/city-shops/${shopId}/books/${bookId}?quantity=${quantity}`,
      { method: 'DELETE' },
    );
    loadInventory(shopId);
  };

  const handleItemRestock = async (
    shopId: number,
    itemId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const interval = Number((form.elements.namedItem('interval') as HTMLInputElement).value);
    const quantity = Number((form.elements.namedItem('quantity') as HTMLInputElement).value);
    await fetch(`/admin/economy/city-shops/${shopId}/items/${itemId}/restock`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval, quantity }),
    });
    form.reset();
    loadInventory(shopId);
  };

  const handleBookRestock = async (
    shopId: number,
    bookId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const interval = Number((form.elements.namedItem('interval') as HTMLInputElement).value);
    const quantity = Number((form.elements.namedItem('quantity') as HTMLInputElement).value);
    await fetch(`/admin/economy/city-shops/${shopId}/books/${bookId}/restock`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval, quantity }),
    });
    form.reset();
    loadInventory(shopId);
  };

  const handleAddBundle = async (
    shopId: number,
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const name = (form.elements.namedItem('name') as HTMLInputElement).value;
    const price = Number(
      (form.elements.namedItem('priceCents') as HTMLInputElement).value,
    );
    const components = (form.elements.namedItem('components') as HTMLInputElement).value
      .split(',')
      .map((p) => {
        const [id, qty] = p.split(':');
        const item_id = Number(id);
        const quantity = Number(qty || '1');
        return item_id ? { item_id, quantity } : null;
      })
      .filter(Boolean) as BundleItem[];
    const promo_starts = (form.elements.namedItem('promoStarts') as HTMLInputElement).value || null;
    const promo_ends = (form.elements.namedItem('promoEnds') as HTMLInputElement).value || null;
    await fetch(`/admin/economy/city-shops/${shopId}/bundles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        price_cents: price,
        items: components,
        promo_starts,
        promo_ends,
      }),
    });
    form.reset();
    loadInventory(shopId);
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">City Shops Admin</h2>
      <SchemaForm
        schemaUrl="/admin/schema/city_shop"
        submitUrl="/admin/economy/city-shops"
        onSubmitted={loadShops}
      />
      <h3 className="text-lg mt-6 mb-2">Existing Shops</h3>
      <ul className="space-y-4">
        {shops.map((shop) => (
          <li key={shop.id} className="border p-2">
            <div className="flex justify-between">
              <span>
                {shop.city} - {shop.name}
              </span>
              <span className="space-x-2">
                <button
                  className="text-blue-500"
                  onClick={() => {
                    const newId = editingId === shop.id ? null : shop.id;
                    setEditingId(newId);
                    if (newId) {
                      loadInventory(shop.id);
                    }
                  }}
                >
                  Edit
                </button>
                <button
                  className="text-red-500"
                  onClick={() => handleDelete(shop.id)}
                >
                  Delete
                </button>
              </span>
            </div>
            {editingId === shop.id && (
              <div className="mt-2 space-y-4">
                <SchemaForm
                  schemaUrl="/admin/schema/city_shop"
                  submitUrl={`/admin/economy/city-shops/${shop.id}`}
                  method="PUT"
                  onSubmitted={() => {
                    loadShops();
                    loadInventory(shop.id);
                  }}
                />
                <div>
                  <h4 className="font-semibold">Items</h4>
                  <form
                    onSubmit={(e) => handleAddItem(shop.id, e)}
                    className="space-x-2 mt-2"
                  >
                    <input
                      name="itemId"
                      type="number"
                      placeholder="Item ID"
                      className="border px-1"
                    />
                    <input
                      name="quantity"
                      type="number"
                      placeholder="Qty"
                      defaultValue={1}
                      className="border px-1"
                    />
                    <input
                      name="priceCents"
                      type="number"
                      placeholder="Price (¢)"
                      className="border px-1"
                    />
                    <button type="submit" className="text-green-500">
                      Add
                    </button>
                  </form>
                  <ul className="mt-2 space-y-1">
                    {(items[shop.id] || []).map((it) => (

                      <li key={it.item_id} className="space-y-1">
                        <div className="flex justify-between">
                          <span>
                            Item {it.item_id} x {it.quantity}
                            {it.restock_interval && it.restock_quantity && (
                              <span className="text-sm text-gray-500 ml-1">
                                (restock {it.restock_quantity} every {it.restock_interval}d)
                              </span>
                            )}
                          </span>
                          <button
                            className="text-red-500"
                            onClick={() =>
                              handleRemoveItem(shop.id, it.item_id, it.quantity)
                            }
                          >
                            Remove
                          </button>
                        </div>
                        <form
                          onSubmit={(e) => handleItemRestock(shop.id, it.item_id, e)}
                          className="space-x-1"
                      <li
                        key={it.item_id}
                        className="flex justify-between items-center space-x-2"
                      >
                        <form
                          onSubmit={(e) =>
                            handleUpdateItem(shop.id, it.item_id, e)
                          }
                          className="flex space-x-2 items-center"
                        >
                          <span>Item {it.item_id}</span>
                          <input
                            name="quantity"
                            type="number"
                            defaultValue={it.quantity}
                            className="border px-1 w-16"
                          />
                          <input
                            name="priceCents"
                            type="number"
                            defaultValue={it.price_cents}
                            className="border px-1 w-24"
                          />
                          <button type="submit" className="text-blue-500">
                            Update
                          </button>
                        </form>
                        <button
                          className="text-red-500"
                          onClick={() =>
                            handleRemoveItem(shop.id, it.item_id, it.quantity)
                          }
                        >
                          <input
                            name="interval"
                            type="number"
                            placeholder="Interval"
                            className="border px-1"
                          />
                          <input
                            name="quantity"
                            type="number"
                            placeholder="Qty"
                            className="border px-1"
                          />
                          <button type="submit" className="text-blue-500">
                            Set
                          </button>
                        </form>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold">Books</h4>
                  <form
                    onSubmit={(e) => handleAddBook(shop.id, e)}
                    className="space-x-2 mt-2"
                  >
                    <input
                      name="bookId"
                      type="number"
                      placeholder="Book ID"
                      className="border px-1"
                    />
                    <input
                      name="quantity"
                      type="number"
                      placeholder="Qty"
                      defaultValue={1}
                      className="border px-1"
                    />
                    <input
                      name="priceCents"
                      type="number"
                      placeholder="Price (¢)"
                      className="border px-1"
                    />
                    <button type="submit" className="text-green-500">
                      Add
                    </button>
                  </form>
                  <ul className="mt-2 space-y-1">
                    {(books[shop.id] || []).map((b) => (

                      <li key={b.book_id} className="space-y-1">
                        <div className="flex justify-between">
                          <span>
                            Book {b.book_id} x {b.quantity}
                            {b.restock_interval && b.restock_quantity && (
                              <span className="text-sm text-gray-500 ml-1">
                                (restock {b.restock_quantity} every {b.restock_interval}d)
                              </span>
                            )}
                          </span>
                          <button
                            className="text-red-500"
                            onClick={() =>
                              handleRemoveBook(shop.id, b.book_id, b.quantity)
                            }
                          >
                            Remove
                          </button>
                        </div>
                        <form
                          onSubmit={(e) => handleBookRestock(shop.id, b.book_id, e)}
                          className="space-x-1"
                      <li
                        key={b.book_id}
                        className="flex justify-between items-center space-x-2"
                      >
                        <form
                          onSubmit={(e) =>
                            handleUpdateBook(shop.id, b.book_id, e)
                          }
                          className="flex space-x-2 items-center"
                        >
                          <span>Book {b.book_id}</span>
                          <input
                            name="quantity"
                            type="number"
                            defaultValue={b.quantity}
                            className="border px-1 w-16"
                          />
                          <input
                            name="priceCents"
                            type="number"
                            defaultValue={b.price_cents}
                            className="border px-1 w-24"
                          />
                          <button type="submit" className="text-blue-500">
                            Update
                          </button>
                        </form>
                        <button
                          className="text-red-500"
                          onClick={() =>
                            handleRemoveBook(shop.id, b.book_id, b.quantity)
                          }

                        >
                          <input
                            name="interval"
                            type="number"
                            placeholder="Interval"
                            className="border px-1"
                          />
                          <input
                            name="quantity"
                            type="number"
                            placeholder="Qty"
                            className="border px-1"
                          />
                          <button type="submit" className="text-blue-500">
                            Set
                          </button>
                        </form>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold">Bundles</h4>
                  <form
                    onSubmit={(e) => handleAddBundle(shop.id, e)}
                    className="space-x-2 mt-2"
                  >
                    <input
                      name="name"
                      type="text"
                      placeholder="Name"
                      className="border px-1"
                    />
                    <input
                      name="components"
                      type="text"
                      placeholder="item:qty,..."
                      className="border px-1"
                    />
                    <input
                      name="priceCents"
                      type="number"
                      placeholder="Price (¢)"
                      className="border px-1"
                    />
                    <input
                      name="promoStarts"
                      type="text"
                      placeholder="Start"
                      className="border px-1"
                    />
                    <input
                      name="promoEnds"
                      type="text"
                      placeholder="End"
                      className="border px-1"
                    />
                    <button type="submit" className="text-green-500">
                      Add
                    </button>
                  </form>
                  <ul className="mt-2 space-y-1">
                    {(bundles[shop.id] || []).map((b) => (
                      <li key={b.id} className="space-y-1">
                        <div className="flex justify-between">
                          <span>
                            {b.name} - {b.price_cents}¢
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {b.items
                            .map((it) => `Item ${it.item_id} x${it.quantity}`)
                            .join(', ')}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CityShopsAdmin;

