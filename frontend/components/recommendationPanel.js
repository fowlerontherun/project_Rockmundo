export async function fetchRecommendations(userId, goals) {
  const res = await fetch('/api/schedule/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, goals })
  });
  if (!res.ok) {
    throw new Error('Failed to fetch recommendations');
  }
  return res.json();
}

export function initRecommendationPanel() {
  const container = document.getElementById('recommendationPanel');
  if (!container) return;

  const form = document.createElement('form');
  const userInput = document.createElement('input');
  userInput.type = 'number';
  userInput.placeholder = 'User ID';
  const goalsInput = document.createElement('input');
  goalsInput.placeholder = 'Goals (comma separated)';
  const submit = document.createElement('button');
  submit.type = 'submit';
  submit.textContent = 'Get Recommendations';

  form.appendChild(userInput);
  form.appendChild(goalsInput);
  form.appendChild(submit);
  container.appendChild(form);

  const list = document.createElement('ul');
  container.appendChild(list);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = parseInt(userInput.value || '0', 10);
    const goals = goalsInput.value
      .split(',')
      .map((g) => g.trim())
      .filter((g) => g);
    let data;
    try {
      data = await fetchRecommendations(userId, goals);
    } catch {
      data = { recommendations: [] };
    }
    list.innerHTML = '';
    data.recommendations.forEach((rec) => {
      const li = document.createElement('li');
      li.textContent = rec;
      list.appendChild(li);
    });
  });
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initRecommendationPanel);
}

export default { initRecommendationPanel, fetchRecommendations };
