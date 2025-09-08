import React, { useState, useCallback, useEffect } from 'react';

declare global {
  interface Window {
    showNotification?: (message: string, type?: 'success' | 'error') => void;
  }
}

interface Note {
  message: string;
  type: 'success' | 'error';
}

const Notification: React.FC<Note & { onClose: () => void }> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);
  return <div className={`notification ${type}`}>{message}</div>;
};

export const NotificationProvider: React.FC = () => {
  const [note, setNote] = useState<Note | null>(null);

  const show = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setNote({ message, type });
  }, []);

  useEffect(() => {
    window.showNotification = show;
    return () => {
      delete window.showNotification;
    };
  }, [show]);

  if (!note) return null;
  return <Notification message={note.message} type={note.type} onClose={() => setNote(null)} />;
};

export default NotificationProvider;
