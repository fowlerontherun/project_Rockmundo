import React, { useEffect, useState } from 'react';

interface SchemaFormProps {
  schemaUrl: string;
  submitUrl: string;
  method?: string;
  onSubmitted?: () => void;
}

const SchemaForm: React.FC<SchemaFormProps> = ({ schemaUrl, submitUrl, method = 'POST', onSubmitted }) => {
  const [schema, setSchema] = useState<any>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    fetch(schemaUrl)
      .then(res => res.json())
      .then(setSchema)
      .catch(() => setSchema(null));
  }, [schemaUrl]);

  if (!schema) {
    return <div>Loading...</div>;
  }

  const properties = schema.properties || {};

  const handleChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch(submitUrl, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    if (onSubmitted) {
      onSubmitted();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {Object.entries(properties).map(([name, prop]) => (
        <div key={name}>
          <label className="block text-sm font-medium mb-1">{name}</label>
          <input
            className="border p-1 w-full"
            type={prop.type === 'number' ? 'number' : 'text'}
            value={formData[name] ?? ''}
            onChange={e => handleChange(name, e.target.value)}
          />
        </div>
      ))}
      <button type="submit" className="px-4 py-2 bg-blue-500 text-white">Submit</button>
    </form>
  );
};

export default SchemaForm;
