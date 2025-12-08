// In-app Support Chat Component
import { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Minimize2, Maximize2, Bot, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'support' | 'bot';
  timestamp: string;
  attachments?: string[];
}

export default function SupportChat() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      // Initial greeting
      setMessages([
        {
          id: '1',
          text: `Hi ${user?.name || 'there'}! 👋 How can I help you today?`,
          sender: 'bot',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  }, [isOpen, user]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    // Simulate bot response (in production, connect to support system)
    setTimeout(() => {
      const botResponse = generateBotResponse(inputText);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: botResponse,
        sender: 'bot',
        timestamp: new Date().toISOString()
      }]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const generateBotResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();

    // Simple keyword matching (in production, use AI or connect to support team)
    if (lowerInput.includes('upload') || lowerInput.includes('photo')) {
      return "To upload photos, go to your gallery and click the 'Upload' button. You can drag and drop multiple photos at once. Need help with a specific upload issue?";
    } else if (lowerInput.includes('billing') || lowerInput.includes('payment') || lowerInput.includes('subscription')) {
      return "For billing questions, visit Settings → Billing. You can view your current plan, payment history, and update your payment method there. Would you like me to connect you with our billing team?";
    } else if (lowerInput.includes('gallery') || lowerInput.includes('share')) {
      return "To share a gallery, open it and click the 'Share' button. You can send a link to your client or enable password protection. What would you like to know more about?";
    } else if (lowerInput.includes('client') || lowerInput.includes('crm')) {
      return "Our CRM helps you manage leads and clients. You can access it from the main navigation. Would you like a quick tour of CRM features?";
    } else if (lowerInput.includes('help') || lowerInput.includes('support')) {
      return "I'm here to help! You can also check our Help Center at help.galerly.com or email support@galerly.com. Would you like me to connect you with a human agent?";
    } else {
      return "Thanks for your message! I'm connecting you with our support team. They'll respond shortly. In the meantime, check out our Help Center for quick answers.";
    }
  };

  const quickReplies = [
    "How do I upload photos?",
    "Billing question",
    "Share gallery with client",
    "Talk to human support"
  ];

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-[#0066CC] text-white rounded-full shadow-2xl hover:bg-[#0052A3] transition-all hover:scale-110 z-40 flex items-center justify-center"
      >
        <MessageCircle className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 z-40 transition-all ${
        isMinimized ? 'w-80' : 'w-96'
      }`}
      style={{ maxHeight: isMinimized ? '60px' : '600px' }}
    >
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#0066CC] to-purple-600 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-white">Galerly Support</h3>
              <p className="text-xs text-white/80">Usually replies in a few minutes</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            >
              {isMinimized ? (
                <Maximize2 className="w-4 h-4 text-white" />
              ) : (
                <Minimize2 className="w-4 h-4 text-white" />
              )}
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex gap-2 max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.sender === 'user'
                        ? 'bg-[#0066CC]'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}>
                      {message.sender === 'user' ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <Bot className="w-4 h-4 text-[#1D1D1F] dark:text-white" />
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div>
                      <div className={`rounded-2xl px-4 py-2 ${
                        message.sender === 'user'
                          ? 'bg-[#0066CC] text-white'
                          : 'bg-gray-100 dark:bg-gray-800 text-[#1D1D1F] dark:text-white'
                      }`}>
                        <p className="text-sm">{message.text}</p>
                      </div>
                      <p className="text-xs text-[#1D1D1F]/40 dark:text-gray-500 mt-1 px-2">
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex gap-2 max-w-[80%]">
                    <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-[#1D1D1F] dark:text-white" />
                    </div>
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-[#1D1D1F]/40 dark:bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-[#1D1D1F]/40 dark:bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-[#1D1D1F]/40 dark:bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Replies */}
            {messages.length <= 1 && (
              <div className="px-4 pb-3 flex flex-wrap gap-2">
                {quickReplies.map((reply, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputText(reply);
                      setTimeout(() => handleSend(), 100);
                    }}
                    className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-[#1D1D1F] dark:text-white text-xs rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="p-4 border-t border-gray-100 dark:border-gray-800">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-800 border-0 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                />
                <button
                  onClick={handleSend}
                  disabled={!inputText.trim()}
                  className="px-4 py-2 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-[#1D1D1F]/40 dark:text-gray-500 mt-2 text-center">
                Powered by Galerly Support
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
