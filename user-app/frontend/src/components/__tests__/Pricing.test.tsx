/**
 * Example React component test
 * Tests for Pricing component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Pricing from '../../components/Pricing';

describe('Pricing Component', () => {
  it('renders pricing section', () => {
    render(
      <BrowserRouter>
        <Pricing />
      </BrowserRouter>
    );
    
    // Check if pricing plans are rendered
    expect(screen.getByText(/Plans & Pricing/i)).toBeInTheDocument();
  });

  it('displays all plan tiers', () => {
    render(
      <BrowserRouter>
        <Pricing />
      </BrowserRouter>
    );
    
    // Check for plan names - using getAllByText since some text appears multiple times
    expect(screen.getAllByText('Free').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Starter').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Plus').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Pro').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Ultimate').length).toBeGreaterThan(0);
  });

  it('shows best value badge on Plus plan', () => {
    render(
      <BrowserRouter>
        <Pricing />
      </BrowserRouter>
    );
    
    expect(screen.getByText('BEST VALUE')).toBeInTheDocument();
  });

  it('displays billing toggle', () => {
    render(
      <BrowserRouter>
        <Pricing />
      </BrowserRouter>
    );
    
    expect(screen.getAllByText('Monthly').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Annual/i).length).toBeGreaterThan(0);
  });
});

