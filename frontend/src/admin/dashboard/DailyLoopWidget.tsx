import React, { useEffect, useState } from 'react';

interface WeeklyReward {
  drop_date: string;
  reward: string;
}

interface DailyStatus {
  login_streak: number;
  current_challenge: string;
  reward_claimed: boolean;
  next_weekly_reward?: WeeklyReward;
}

const DailyLoopWidget: React.FC = () => {
  const [status, setStatus] = useState<DailyStatus | null>(null);

  useEffect(() => {
    fetch('/api/daily/status/1')
      .then((res) => res.json())
      .then((data) => setStatus(data));
  }, []);

  if (!status) {
    return <div>Loading...</div>;
  }

  return (
    <div className="mb-4">
      <h3 className="text-lg font-semibold">Daily Loop</h3>
      <p>Streak: {status.login_streak}</p>
      <p>Challenge: {status.current_challenge}</p>
      {status.next_weekly_reward && (
        <p>Next Drop: {status.next_weekly_reward.reward}</p>
      )}
    </div>
  );
};

export default DailyLoopWidget;
