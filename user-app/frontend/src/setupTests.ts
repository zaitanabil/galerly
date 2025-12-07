import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Runs a cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
});

// Mock matchMedia for GSAP/ScrollTrigger
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

// Mock video.js for VideoPlayer tests
vi.mock('video.js', () => {
  const mockPlayer = {
    play: vi.fn().mockResolvedValue(undefined),
    pause: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    currentTime: vi.fn().mockReturnValue(0),
    duration: vi.fn().mockReturnValue(100),
    ready: vi.fn((callback) => callback()),
  };

  const videojs = vi.fn(() => mockPlayer) as any;
  videojs.log = vi.fn();
  videojs.getPlayers = vi.fn().mockReturnValue({});
  
  return { default: videojs };
});

