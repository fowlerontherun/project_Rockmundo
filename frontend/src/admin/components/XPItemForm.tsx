import React from 'react';
import SchemaForm from './SchemaForm';

const XPItemForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/xp_item" submitUrl="/admin/xp/items" />
);

export default XPItemForm;
