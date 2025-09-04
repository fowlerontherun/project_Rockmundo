import React from 'react';

interface NavItem {
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'NPCs', href: '/admin/npcs' },
  { label: 'NPC Dialogue', href: '/admin/npcs/dialogue' },
  { label: 'Quests', href: '/admin/quests' },
  { label: 'Economy', href: '/admin/economy' },
  { label: 'City Shops', href: '/admin/economy/city-shops' },
  { label: 'XP', href: '/admin/xp' },
  { label: 'XP Events', href: '/admin/xp-events' },
  { label: 'XP Items', href: '/admin/xp-items' },
  { label: 'Events', href: '/admin/events' },
  { label: 'Books', href: '/admin/learning/books' },
  { label: 'Tutorials', href: '/admin/learning/tutorials' },
  { label: 'Tutors', href: '/admin/learning/tutors' },
  { label: 'Mentors', href: '/admin/learning/mentors' },
  { label: 'Venues', href: '/admin/venues' },
  { label: 'Audit Logs', href: '/admin/audit' },
  { label: 'Modding', href: '/admin/modding' },
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
