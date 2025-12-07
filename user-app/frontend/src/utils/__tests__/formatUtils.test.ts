import { describe, it, expect } from 'vitest';
import { formatNumber, formatFileSize, truncateText, getInitials } from '../formatUtils';

describe('formatUtils', () => {
  it('formats numbers with commas', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1000000)).toBe('1,000,000');
    expect(formatNumber(0)).toBe('0');
  });

  it('formats file sizes correctly', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1024 * 1024)).toBe('1 MB');
    expect(formatFileSize(1024 * 1024 * 5)).toBe('5 MB');
    expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
  });

  it('truncates text correctly', () => {
    const text = 'Hello world, this is a long sentence.';
    expect(truncateText(text, 10)).toBe('Hello worl...');
    expect(truncateText(text, 50)).toBe(text);
  });

  it('gets initials from name', () => {
    expect(getInitials('John Doe')).toBe('JD');
    expect(getInitials('Jane')).toBe('J');
    expect(getInitials('John Middle Doe')).toBe('JM'); // Takes first 2 parts by default implementation
  });
});

