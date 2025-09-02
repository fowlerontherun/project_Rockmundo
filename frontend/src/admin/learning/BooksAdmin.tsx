import React, { useEffect, useState } from 'react';
import SchemaForm from '../components/SchemaForm';

interface Book {
  id: number;
  title: string;
  genre: string;
  rarity: string;
  max_skill_level: number;
}

const BooksAdmin: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadBooks = () => {
    fetch('/admin/learning/books')
      .then(res => res.json())
      .then(setBooks);
  };

  useEffect(() => {
    loadBooks();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`/admin/learning/books/${id}`, { method: 'DELETE' });
    setEditingId(null);
    loadBooks();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Books Admin</h2>
      <SchemaForm
        schemaUrl="/admin/schema/book"
        submitUrl="/admin/learning/books"
        onSubmitted={loadBooks}
      />
      <h3 className="text-lg mt-6 mb-2">Existing Books</h3>
      <ul className="space-y-4">
        {books.map(book => (
          <li key={book.id} className="border p-2">
            <div className="flex justify-between">
              <span>
                {book.title} ({book.genre}) - {book.rarity} max:{' '}
                {book.max_skill_level}
              </span>
              <span className="space-x-2">
                <button
                  className="text-blue-500"
                  onClick={() =>
                    setEditingId(editingId === book.id ? null : book.id)
                  }
                >
                  Edit
                </button>
                <button
                  className="text-red-500"
                  onClick={() => handleDelete(book.id)}
                >
                  Delete
                </button>
              </span>
            </div>
            {editingId === book.id && (
              <div className="mt-2">
                <SchemaForm
                  schemaUrl="/admin/schema/book"
                  submitUrl={`/admin/learning/books/${book.id}`}
                  method="PUT"
                  onSubmitted={loadBooks}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default BooksAdmin;
