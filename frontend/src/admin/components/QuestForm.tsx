import React from 'react';
import SchemaForm from './SchemaForm';

const QuestForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/quest" submitUrl="/admin/quests" />
);

export default QuestForm;
