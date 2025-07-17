/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConversationHistory } from '../conversation-history-consolidated';
import { Conversation } from '@/lib/types';

// Mock Lucide React icons
jest.mock('lucide-react', () => ({
  Loader2: ({ className }: { className?: string }) => <div className={className} data-testid="loader" />,
  Trash2: ({ className }: { className?: string }) => <div className={className} data-testid="trash-icon" />,
  History: ({ className }: { className?: string }) => <div className={className} data-testid="history-icon" />,
}));

describe('ConversationHistory', () => {
  const mockConversations: Conversation[] = [
    {
      thread_id: 'thread-1',
      preview: 'First conversation about React',
      last_message_ts: '2025-01-17T10:30:00.000Z',
    },
    {
      thread_id: 'thread-2',
      preview: 'Second conversation about TypeScript',
      last_message_ts: '2025-01-16T15:45:00.000Z',
    },
    {
      thread_id: 'thread-3',
      preview: 'Third conversation with no preview',
      last_message_ts: null,
    },
  ];

  const defaultProps = {
    conversations: mockConversations,
    isLoading: false,
    onSelectConversation: jest.fn(),
    onDeleteConversation: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the conversation history accordion', () => {
      render(<ConversationHistory {...defaultProps} />);
      
      expect(screen.getByText('Chat History')).toBeInTheDocument();
      expect(screen.getByTestId('history-icon')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      render(<ConversationHistory {...defaultProps} isLoading={true} />);
      
      expect(screen.getByTestId('loader')).toBeInTheDocument();
      expect(screen.getByTestId('loader')).toHaveClass('animate-spin');
    });

    it('shows empty state when no conversations', () => {
      render(<ConversationHistory {...defaultProps} conversations={[]} />);
      
      expect(screen.getByText('No previous conversations')).toBeInTheDocument();
    });
  });

  describe('Conversation List', () => {
    it('renders all conversations', () => {
      render(<ConversationHistory {...defaultProps} />);
      
      expect(screen.getByText('First conversation about React')).toBeInTheDocument();
      expect(screen.getByText('Second conversation about TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Third conversation with no preview')).toBeInTheDocument();
    });

    it('shows "No preview" for conversations without preview', () => {
      const conversationsWithoutPreview: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: '',
          last_message_ts: '2025-01-17T10:30:00.000Z',
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={conversationsWithoutPreview} />);
      
      expect(screen.getByText('No preview')).toBeInTheDocument();
    });

    it('calls onSelectConversation when conversation is clicked', () => {
      const mockOnSelect = jest.fn();
      render(<ConversationHistory {...defaultProps} onSelectConversation={mockOnSelect} />);
      
      fireEvent.click(screen.getByText('First conversation about React'));
      
      expect(mockOnSelect).toHaveBeenCalledWith('thread-1');
    });

    it('calls onDeleteConversation when delete button is clicked', () => {
      const mockOnDelete = jest.fn();
      render(<ConversationHistory {...defaultProps} onDeleteConversation={mockOnDelete} />);
      
      const deleteButtons = screen.getAllByTestId('trash-icon');
      fireEvent.click(deleteButtons[0]);
      
      expect(mockOnDelete).toHaveBeenCalledWith('thread-1');
    });

    it('prevents conversation selection when delete button is clicked', () => {
      const mockOnSelect = jest.fn();
      const mockOnDelete = jest.fn();
      
      render(
        <ConversationHistory 
          {...defaultProps} 
          onSelectConversation={mockOnSelect}
          onDeleteConversation={mockOnDelete}
        />
      );
      
      const deleteButtons = screen.getAllByTestId('trash-icon');
      fireEvent.click(deleteButtons[0]);
      
      expect(mockOnDelete).toHaveBeenCalledWith('thread-1');
      expect(mockOnSelect).not.toHaveBeenCalled();
    });
  });

  describe('Date Formatting', () => {
    beforeEach(() => {
      // Mock current time for consistent testing
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-17T12:00:00.000Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('formats recent timestamps as relative time', () => {
      const recentConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'Recent conversation',
          last_message_ts: '2025-01-17T11:30:00.000Z', // 30 minutes ago
        },
        {
          thread_id: 'thread-2',
          preview: 'Very recent conversation',
          last_message_ts: '2025-01-17T11:58:00.000Z', // 2 minutes ago
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={recentConversations} />);
      
      expect(screen.getByText('30 minutes ago')).toBeInTheDocument();
      expect(screen.getByText('2 minutes ago')).toBeInTheDocument();
    });

    it('formats older timestamps as absolute dates', () => {
      const olderConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'Yesterday conversation',
          last_message_ts: '2025-01-16T10:00:00.000Z', // Yesterday
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={olderConversations} />);
      
      // Should show formatted date instead of relative time
      expect(screen.getByText(/Jan 16/)).toBeInTheDocument();
    });

    it('handles invalid timestamps gracefully', () => {
      const invalidTimestampConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'Invalid timestamp conversation',
          last_message_ts: 'invalid-date',
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={invalidTimestampConversations} />);
      
      expect(screen.getByText('Invalid date')).toBeInTheDocument();
    });

    it('handles null timestamps', () => {
      const nullTimestampConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'No timestamp conversation',
          last_message_ts: null,
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={nullTimestampConversations} />);
      
      expect(screen.getByText('No date')).toBeInTheDocument();
    });
  });

  describe('Debug Mode', () => {
    it('renders differently in debug mode', () => {
      render(<ConversationHistory {...defaultProps} debugMode={true} />);
      
      // In debug mode, the accordion trigger should have different styling
      const trigger = screen.getByRole('button');
      expect(trigger).toHaveClass('py-2', 'px-4', 'hover:no-underline');
    });

    it('logs debug information in debug mode', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      render(<ConversationHistory {...defaultProps} debugMode={true} />);
      
      // Should log conversation details in debug mode
      expect(consoleSpy).toHaveBeenCalledWith(
        'Conversation:',
        expect.objectContaining({
          thread_id: 'thread-1',
          preview: 'First conversation about React',
        })
      );
      
      consoleSpy.mockRestore();
    });

    it('shows simple date format in debug mode', () => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-17T12:00:00.000Z'));

      const debugConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'Debug conversation',
          last_message_ts: '2025-01-17T10:30:00.000Z',
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={debugConversations} debugMode={true} />);
      
      // In debug mode, should show simple format instead of relative time
      expect(screen.getByText(/Jan 17/)).toBeInTheDocument();
      
      jest.useRealTimers();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<ConversationHistory {...defaultProps} />);
      
      // Check for accordion structure
      expect(screen.getByRole('button')).toHaveAttribute('aria-expanded');
    });

    it('has proper title attributes for long previews', () => {
      const longPreviewConversations: Conversation[] = [
        {
          thread_id: 'thread-1',
          preview: 'This is a very long conversation preview that should be truncated in the display but available in the title attribute',
          last_message_ts: '2025-01-17T10:30:00.000Z',
        },
      ];

      render(<ConversationHistory {...defaultProps} conversations={longPreviewConversations} />);
      
      const conversationElement = screen.getByText(/This is a very long conversation/);
      expect(conversationElement.closest('[title]')).toHaveAttribute(
        'title',
        'This is a very long conversation preview that should be truncated in the display but available in the title attribute'
      );
    });
  });

  describe('Hover Effects', () => {
    it('shows delete button on hover', () => {
      render(<ConversationHistory {...defaultProps} />);
      
      const conversationElements = screen.getAllByText(/conversation/);
      const firstConversation = conversationElements[0].closest('.group');
      
      expect(firstConversation).toHaveClass('group');
      
      // Delete button should have opacity-0 initially and opacity-100 on group-hover
      const deleteButton = firstConversation?.querySelector('button');
      expect(deleteButton).toHaveClass('opacity-0', 'group-hover:opacity-100');
    });
  });
});