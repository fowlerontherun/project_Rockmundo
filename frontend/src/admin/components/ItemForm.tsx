import React from 'react';
import SchemaForm from './SchemaForm';

const ItemForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/item" submitUrl="/admin/items" />
);

export default ItemForm;
