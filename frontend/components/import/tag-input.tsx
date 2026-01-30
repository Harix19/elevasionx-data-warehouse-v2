'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface TagInputProps {
  label: string;
  description?: string;
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}

export function TagInput({
  label,
  description,
  value,
  onChange,
  placeholder = "e.g. apollo-export, jan-2026, campaign-xyz",
}: TagInputProps) {
  const inputValue = value.join(', ');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tags = e.target.value
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag !== '');
    onChange(tags);
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold">{label}</Label>
      {description && <p className="text-xs text-muted-foreground mb-1">{description}</p>}
      <Input
        value={inputValue}
        onChange={handleChange}
        placeholder={placeholder}
      />
      <div className="flex flex-wrap gap-1 mt-1">
        {value.map((tag, i) => (
          <span
            key={i}
            className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
