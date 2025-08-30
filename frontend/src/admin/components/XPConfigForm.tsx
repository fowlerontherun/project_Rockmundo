import React from 'react';
import SchemaForm from './SchemaForm';

const XPConfigForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/xp" submitUrl="/admin/xp/config" method="PUT" />
);

export default XPConfigForm;
