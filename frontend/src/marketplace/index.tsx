import React from 'react';
import ReactDOM from 'react-dom/client';
import Marketplace from './Marketplace';
import '../index.css';

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<Marketplace />);
}
