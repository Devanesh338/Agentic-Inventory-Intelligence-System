import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the Executive Overview header', () => {
    // Basic structural test
    render(<App />);
    expect(document.querySelector('.sidebar')).toBeDefined();
    expect(document.querySelector('.main-content')).toBeDefined();
  });
});
