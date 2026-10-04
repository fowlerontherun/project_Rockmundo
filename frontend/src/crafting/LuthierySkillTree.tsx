import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../utils/api.js';

type Requirement = { skill: string; required_level: number; current_level: number };
type Reward = { level: number; key: string; name: string };
type SkillNode = {
  id: number; key: string; label: string; description: string; level: number;
  locked: boolean; missing_requirements: Requirement[];
  learning_methods: string[];
};
type Tree = {
  category: string;
  skills: SkillNode[];
  rewards: Record<string, { unlocked: Reward[]; upcoming: Reward[] }>;
};

const LuthierySkillTree: React.FC = () => {
  const [tree, setTree] = useState<Tree | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/learning/luthiery/tree')
      .then(async (res) => {
        if (!res.ok) throw new Error('Unable to load Luthiery progression');
        return res.json();
      })
      .then(setTree)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p role="alert">{error}</p>;
  if (!tree) return <p>Loading Luthiery skills…</p>;

  return (
    <section aria-labelledby="luthiery-heading">
      <h2 id="luthiery-heading">Craftsmanship — Luthiery</h2>
      <div className="space-y-3">
        {tree.skills.map((skill) => (
          <article key={skill.key} className="border rounded p-3">
            <h3>{skill.label} — Level {skill.level}</h3>
            <p>{skill.description}</p>
            {skill.locked ? (
              <p>
                Locked: {skill.missing_requirements.map((r) =>
                  `${r.skill.replaceAll('_', ' ')} ${r.current_level}/${r.required_level}`
                ).join(', ')}
              </p>
            ) : (
              <p>Available learning: {skill.learning_methods.join(', ')}</p>
            )}
          </article>
        ))}
      </div>
      <h3 className="mt-4">Upcoming Luthiery unlocks</h3>
      {Object.entries(tree.rewards).map(([category, rewards]) => (
        <div key={category}>
          <strong>{category.replace(/^./, (c) => c.toUpperCase())}</strong>
          <ul>
            {rewards.upcoming.slice(0, 3).map((reward) => (
              <li key={reward.key}>Level {reward.level}: {reward.name}</li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
};

export default LuthierySkillTree;
