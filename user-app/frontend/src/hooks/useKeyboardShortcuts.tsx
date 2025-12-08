// Keyboard Shortcuts System - Respects photo scroll context
import { useEffect, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  description: string;
  action: () => void;
  contexts?: string[]; // Which pages/contexts this shortcut applies to
  disableInPhotoView?: boolean; // Disable when in TikTok-style photo view
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
  isPhotoView?: boolean; // Indicates if user is in TikTok-style photo scrolling
}

export function useKeyboardShortcuts({ shortcuts, enabled = true, isPhotoView = false }: UseKeyboardShortcutsOptions) {
  const location = useLocation();

  const handleKeyPress = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    // Don't trigger shortcuts when typing in inputs
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }

    // Find matching shortcut
    const shortcut = shortcuts.find(s => {
      // Skip if disabled in photo view
      if (isPhotoView && s.disableInPhotoView) {
        return false;
      }

      // Check if shortcut matches current context
      if (s.contexts && !s.contexts.some(ctx => location.pathname.includes(ctx))) {
        return false;
      }

      // Match key combination
      const keyMatches = event.key.toLowerCase() === s.key.toLowerCase();
      const ctrlMatches = s.ctrlKey ? event.ctrlKey : true;
      const metaMatches = s.metaKey ? event.metaKey : true;
      const shiftMatches = s.shiftKey ? event.shiftKey : true;

      return keyMatches && ctrlMatches && metaMatches && shiftMatches;
    });

    if (shortcut) {
      event.preventDefault();
      shortcut.action();
    }
  }, [shortcuts, enabled, location.pathname, isPhotoView]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);
}

// Keyboard Shortcuts Help Modal
export function KeyboardShortcutsModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null;

  const shortcuts = [
    {
      category: 'Navigation',
      items: [
        { keys: ['⌘', 'K'], description: 'Open global search' },
        { keys: ['G', 'D'], description: 'Go to Dashboard' },
        { keys: ['G', 'G'], description: 'Go to Galleries' },
        { keys: ['G', 'C'], description: 'Go to CRM' },
        { keys: ['G', 'S'], description: 'Go to Settings' },
      ]
    },
    {
      category: 'Actions',
      items: [
        { keys: ['N'], description: 'New gallery' },
        { keys: ['⌘', 'S'], description: 'Save changes' },
        { keys: ['⌘', 'U'], description: 'Upload photos' },
        { keys: ['Esc'], description: 'Close modal/dialog' },
      ]
    },
    {
      category: 'Gallery View',
      items: [
        { keys: ['←', '→'], description: 'Navigate between photos' },
        { keys: ['Space'], description: 'Play/Pause video' },
        { keys: ['F'], description: 'Toggle fullscreen' },
        { keys: ['I'], description: 'Show photo info' },
      ]
    },
    {
      category: 'Photo Scroll View',
      items: [
        { keys: ['↑', '↓'], description: 'Scroll photos (TikTok style)' },
        { keys: ['Space'], description: 'Reserved for video playback' },
        { keys: ['Esc'], description: 'Exit photo view' },
      ]
    },
    {
      category: 'Editing',
      items: [
        { keys: ['⌘', 'Z'], description: 'Undo' },
        { keys: ['⌘', '⇧', 'Z'], description: 'Redo' },
        { keys: ['⌘', 'A'], description: 'Select all' },
        { keys: ['Delete'], description: 'Delete selected' },
      ]
    },
    {
      category: 'Other',
      items: [
        { keys: ['?'], description: 'Show keyboard shortcuts' },
        { keys: ['⌘', '/'], description: 'Toggle command palette' },
      ]
    }
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-medium text-[#1D1D1F] dark:text-white">
            Keyboard Shortcuts
          </h2>
          <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400 mt-1">
            Work faster with keyboard shortcuts
          </p>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {shortcuts.map((category) => (
              <div key={category.category}>
                <h3 className="text-sm font-semibold text-[#1D1D1F]/40 dark:text-gray-400 uppercase mb-3">
                  {category.category}
                </h3>
                <div className="space-y-2">
                  {category.items.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-sm text-[#1D1D1F] dark:text-white">
                        {item.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {item.keys.map((key, keyIdx) => (
                          <kbd
                            key={keyIdx}
                            className="px-2 py-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-xs font-mono text-[#1D1D1F] dark:text-white"
                          >
                            {key}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <p className="text-xs text-[#1D1D1F]/60 dark:text-gray-400">
            Press <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">?</kbd> anytime to view this help
          </p>
        </div>
      </div>
    </div>
  );
}

// Global keyboard shortcuts hook for the entire app
export function useGlobalKeyboardShortcuts(navigate: any, isPhotoView: boolean = false) {
  const [showHelp, setShowHelp] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  useKeyboardShortcuts({
    isPhotoView,
    shortcuts: [
      // Help
      {
        key: '?',
        description: 'Show keyboard shortcuts',
        action: () => setShowHelp(true),
        disableInPhotoView: false
      },
      // Search
      {
        key: 'k',
        metaKey: true,
        description: 'Open search',
        action: () => setShowSearch(true),
        disableInPhotoView: false
      },
      // Navigation - disable in photo view
      {
        key: 'd',
        shiftKey: true,
        description: 'Go to Dashboard',
        action: () => navigate('/dashboard'),
        disableInPhotoView: true
      },
      {
        key: 'g',
        shiftKey: true,
        description: 'Go to Galleries',
        action: () => navigate('/galleries'),
        disableInPhotoView: true
      },
      {
        key: 'c',
        shiftKey: true,
        description: 'Go to CRM',
        action: () => navigate('/crm'),
        contexts: ['/dashboard', '/galleries', '/crm'],
        disableInPhotoView: true
      },
      {
        key: 's',
        shiftKey: true,
        description: 'Go to Settings',
        action: () => navigate('/settings'),
        disableInPhotoView: true
      },
      // New items
      {
        key: 'n',
        description: 'New gallery',
        action: () => navigate('/new-gallery'),
        contexts: ['/dashboard', '/galleries'],
        disableInPhotoView: true
      }
    ]
  });

  return { showHelp, setShowHelp, showSearch, setShowSearch };
}

// Export for use in components
export default useKeyboardShortcuts;
