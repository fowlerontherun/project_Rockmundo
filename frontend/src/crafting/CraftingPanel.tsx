import React, { useEffect, useState } from 'react';

interface Recipe {
  name: string;
  result_item_id: number;
  components: Record<number, number>;
}

const CraftingPanel: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selected, setSelected] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('/crafting/recipes')
      .then((r) => r.json())
      .then((data) => setRecipes(data));
  }, []);

  const craft = async () => {
    setMessage('');
    const res = await fetch(`/crafting/craft/${selected}`, { method: 'POST' });
    if (res.ok) {
      setMessage('Crafting complete!');
    } else {
      const err = await res.json();
      setMessage(err.detail || 'Crafting failed');
    }
  };

  return (
    <div>
      <select value={selected} onChange={(e) => setSelected(e.target.value)}>
        <option value="">Select recipe</option>
        {recipes.map((r) => (
          <option key={r.name} value={r.name}>
            {r.name}
          </option>
        ))}
      </select>
      <button disabled={!selected} onClick={craft} className="ml-2">
        Craft
      </button>
      {message && <p className="mt-2">{message}</p>}
    </div>
  );
};

export default CraftingPanel;
