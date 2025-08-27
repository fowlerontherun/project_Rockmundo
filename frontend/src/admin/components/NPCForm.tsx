import React from 'react';
import SchemaForm from './SchemaForm';

const NPCForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/npc" submitUrl="/admin/npcs" />
);

export default NPCForm;
