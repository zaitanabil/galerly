import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import CustomDomainHelpPage from '../CustomDomainHelpPage';

// Mock components
vi.mock('../../components/Header', () => ({
  default: () => <div>Header</div>,
}));

vi.mock('../../components/Footer', () => ({
  default: () => <div>Footer</div>,
}));

describe('CustomDomainHelpPage', () => {
  const renderPage = () => {
    return render(
      <BrowserRouter>
        <CustomDomainHelpPage />
      </BrowserRouter>
    );
  };

  it('renders the page title', () => {
    renderPage();
    expect(screen.getByText('Custom Domain Guide')).toBeInTheDocument();
  });

  it('displays quick start steps', () => {
    renderPage();
    expect(screen.getByText(/Go to Portfolio Settings/)).toBeInTheDocument();
    expect(screen.getByText(/Click "Auto-Setup"/)).toBeInTheDocument();
    expect(screen.getByText(/Add DNS records/)).toBeInTheDocument();
  });

  it('shows feature cards', () => {
    renderPage();
    expect(screen.getByText('Free SSL Certificate')).toBeInTheDocument();
    expect(screen.getByText('Global CDN')).toBeInTheDocument();
    expect(screen.getByText('Auto-Renewal')).toBeInTheDocument();
  });

  it('includes category filters', () => {
    renderPage();
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Getting Started')).toBeInTheDocument();
    expect(screen.getByText('DNS Setup')).toBeInTheDocument();
    expect(screen.getByText('Troubleshooting')).toBeInTheDocument();
  });

  it('displays external resource links', () => {
    renderPage();
    expect(screen.getByText('Check DNS Propagation')).toBeInTheDocument();
    expect(screen.getByText('AWS Certificate Manager Docs')).toBeInTheDocument();
    expect(screen.getByText('CloudFront CDN Documentation')).toBeInTheDocument();
  });

  it('shows support CTA', () => {
    renderPage();
    expect(screen.getByText('Still Need Help?')).toBeInTheDocument();
    expect(screen.getByText('Contact Support')).toBeInTheDocument();
  });

  it('has correct external links', () => {
    renderPage();
    const dnsLink = screen.getByText('Check DNS Propagation').closest('a');
    expect(dnsLink).toHaveAttribute('href', 'https://www.whatsmydns.net');
    expect(dnsLink).toHaveAttribute('target', '_blank');
    expect(dnsLink).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
