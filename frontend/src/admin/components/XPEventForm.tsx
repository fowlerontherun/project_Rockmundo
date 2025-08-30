import React from 'react';
import SchemaForm from './SchemaForm';

const XPEventForm: React.FC = () => (
  <SchemaForm schemaUrl="/admin/schema/xp_event" submitUrl="/admin/xp/events" />
);

export default XPEventForm;
