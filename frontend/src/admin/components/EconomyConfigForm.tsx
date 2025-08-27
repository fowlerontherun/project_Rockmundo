import React from 'react';
import SchemaForm from './SchemaForm';

const EconomyConfigForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/economy" submitUrl="/admin/economy/config" method="PUT" />
);

export default EconomyConfigForm;
