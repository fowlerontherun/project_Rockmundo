import React from 'react';
import MetricsWidget from './MetricsWidget';
import AlertsWidget from './AlertsWidget';
import RbacControls from './RbacControls';
import DailyLoopWidget from './DailyLoopWidget';

const Dashboard: React.FC = () => (
  <div className="mt-6">
    <DailyLoopWidget />
    <h2 className="text-xl font-semibold mb-2">Monitoring</h2>
    <MetricsWidget />
    <h3 className="text-lg font-semibold">Alerts</h3>
    <AlertsWidget />
    <RbacControls />
  </div>
);

export default Dashboard;
