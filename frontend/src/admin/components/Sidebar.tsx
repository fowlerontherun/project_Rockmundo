import React from 'react';

interface NavItem {
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { label: 'NPCs', href: '/admin/npcs' },
  { label: 'Quests', href: '/admin/quests' },
  { label: 'Economy', href: '/admin/economy' },
  { label: 'Venues', href: '/admin/venues' },
];

const Sidebar: React.FC = () => (
  <aside className="w-64 bg-gray-800 text-white h-screen p-4">
    <nav>
      <ul>
        {navItems.map((item) => (
          <li key={item.href} className="mb-2">
            <a
              href={item.href}
              className="block px-2 py-1 rounded hover:bg-gray-700"
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  </aside>
);

export default Sidebar;
