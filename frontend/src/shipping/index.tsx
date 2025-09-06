import React from 'react';
import ReactDOM from 'react-dom/client';
import ShippingPanel from './ShippingPanel';
import '../index.css';

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<ShippingPanel />);
}
