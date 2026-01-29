import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Zap, Brain, Settings, ChevronDown, Globe, Mic, FileText, Search, Youtube, Image, Eye, BookOpen } from 'lucide-react';
import VoiceChat from './VoiceChat';
import DocumentChat from './DocumentChat';
import WebSearch from './WebSearch';
import YouTubeChat from './YouTubeChat';
import ImageGenerator from './ImageGenerator';
import VisionAnalysis from './VisionAnalysis';

const API_BASE = '/api';

// Provider colors and icons
const PROVIDER_STYLES = {
  claude: { color: '#D97706', name: 'Claude', icon: '' },
  openai: { color: '#10B981', name: 'GPT-4', icon: '' },
  gemini: { color: '#3B82F6', name: 'Gemini', icon: '' },
  huggingface: { color: '#FBBF24', name: 'HuggingFace', icon: '' },
  perplexity: { color: '#8B5CF6', name: 'Perplexity', icon: '' },
  bytez: { color: '#EC4899', name: 'Bytez', icon: '' },
  openrouter: { color: '#FF6B35', name: 'OpenRouter', icon: '' },
  groq: { color: '#F97316', name: 'Groq', icon: '' },
  cerebras: { color: '#06B6D4', name: 'Cerebras', icon: '' },
  deepseek: { color: '#6366F1', name: 'DeepSeek', icon: '' },
};

// Feature buttons configuration
const FEATURES = [
  { id: 'voice', name: 'Languages', icon: Globe, color: 'from-purple-600 to-pink-600', description: 'Learn languages with voice' },
  { id: 'documents', name: 'Documents', icon: FileText, color: 'from-green-500 to-emerald-600', description: 'Chat with your PDFs' },
  { id: 'search', name: 'Search', icon: Search, color: 'from-blue-500 to-cyan-600', description: 'Search the web' },
  { id: 'youtube', name: 'YouTube', icon: Youtube, color: 'from-red-500 to-red-600', description: 'Chat with videos' },
  { id: 'image', name: 'Images', icon: Image, color: 'from-purple-500 to-pink-600', description: 'Generate images' },
  { id: 'vision', name: 'Vision', icon: Eye, color: 'from-cyan-500 to-blue-600', description: 'Analyze images' },
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('auto');
  const [showProviderMenu, setShowProviderMenu] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchProviders();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchProviders = async () => {
    try {
      const res = await fetch(`${API_BASE}/providers`);
      const data = await res.json();
      setProviders(data);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          conversation_history: messages,
          preferred_provider: selectedProvider === 'auto' ? null : selectedProvider,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to get response');
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        provider: data.provider,
        model: data.model,
        category: data.category,
        routing_explanation: data.routing_explanation,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderFeatureModal = () => {
    switch (activeFeature) {
      case 'voice':
        return <VoiceChat onClose={() => setActiveFeature(null)} />;
      case 'documents':
        return <DocumentChat onClose={() => setActiveFeature(null)} />;
      case 'search':
        return <WebSearch onClose={() => setActiveFeature(null)} />;
      case 'youtube':
        return <YouTubeChat onClose={() => setActiveFeature(null)} />;
      case 'image':
        return <ImageGenerator onClose={() => setActiveFeature(null)} />;
      case 'vision':
        return <VisionAnalysis onClose={() => setActiveFeature(null)} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {activeFeature && renderFeatureModal()}

      <header className="flex items-center justify-between px-6 py-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AI Hub</h1>
            <p className="text-xs text-slate-400">Multi-Model AI Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setShowProviderMenu(!showProviderMenu)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="hidden sm:inline">{selectedProvider === 'auto' ? 'Auto' : PROVIDER_STYLES[selectedProvider]?.name}</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {showProviderMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
                <button
                  onClick={() => { setSelectedProvider('auto'); setShowProviderMenu(false); }}
                  className="w-full px-4 py-3 text-left hover:bg-slate-700 flex items-center gap-3"
                >
                  <Sparkles className="w-5 h-5 text-yellow-400" />
                  <div>
                    <div className="font-medium">Auto Route</div>
                    <div className="text-xs text-slate-400">Best model for your query</div>
                  </div>
                </button>
                <div className="border-t border-slate-700" />
                {providers.filter(p => p.available).map(provider => (
                  <button
                    key={provider.name}
                    onClick={() => {
                      const key = Object.keys(PROVIDER_STYLES).find(k =>
                        PROVIDER_STYLES[k].name === provider.name || provider.name.toLowerCase().includes(k)
                      );
                      setSelectedProvider(key || 'auto');
                      setShowProviderMenu(false);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-slate-700 flex items-center gap-3"
                  >
                    <span className="text-xl">{PROVIDER_STYLES[provider.name.toLowerCase()]?.icon || ''}</span>
                    <div>
                      <div className="font-medium">{provider.name}</div>
                      <div className="text-xs text-slate-400">{provider.strengths?.slice(0, 2).join(', ')}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 border-b border-slate-700/50 overflow-x-auto">
        {FEATURES.map((feature) => (
          <button
            key={feature.id}
            onClick={() => setActiveFeature(feature.id)}
            className={`flex items-center gap-2 px-4 py-2 bg-gradient-to-r ${feature.color} hover:opacity-90 rounded-lg transition-all whitespace-nowrap`}
          >
            <feature.icon className="w-4 h-4" />
            <span className="text-sm font-medium">{feature.name}</span>
          </button>
        ))}
      </div>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-4 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-full mb-6">
              <Brain className="w-16 h-16 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Welcome to AI Hub</h2>
            <p className="text-slate-400 max-w-md mb-6">
              One interface, all AI models. Chat with me or use the feature buttons above.
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl">
              {FEATURES.map((feature) => (
                <button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
                  className="flex flex-col items-center p-4 bg-slate-800 hover:bg-slate-700 rounded-xl border border-slate-700 transition-colors"
                >
                  <div className={`p-2 bg-gradient-to-br ${feature.color} rounded-lg mb-2`}>
                    <feature.icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-medium text-sm">{feature.name}</span>
                  <span className="text-xs text-slate-400 mt-1">{feature.description}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 message-enter ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: msg.provider ? PROVIDER_STYLES[msg.provider]?.color + '30' : '#475569' }}
              >
                {msg.provider ? PROVIDER_STYLES[msg.provider]?.icon : <Bot className="w-5 h-5" />}
              </div>
            )}

            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-1' : ''}`}>
              <div
                className={`px-4 py-3 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.isError
                    ? 'bg-red-900/50 border border-red-700'
                    : 'bg-slate-800 border border-slate-700'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>

              {msg.provider && (
                <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                  <span
                    className="px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: PROVIDER_STYLES[msg.provider]?.color + '20', color: PROVIDER_STYLES[msg.provider]?.color }}
                  >
                    {PROVIDER_STYLES[msg.provider]?.name}
                  </span>
                  <span></span>
                  <span>{msg.category}</span>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 message-enter">
            <div className="w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 animate-pulse" />
            </div>
            <div className="px-4 py-3 bg-slate-800 rounded-2xl border border-slate-700">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      <footer className="p-4 bg-slate-800 border-t border-slate-700">
        <div className="max-w-4xl mx-auto flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask anything... I'll route to the best AI"
            className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl resize-none focus:outline-none focus:border-blue-500 transition-colors"
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-xl transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-center text-xs text-slate-500 mt-2">
          AI Hub automatically selects the best AI model for your query
        </p>
      </footer>
    </div>
  );
}

export default App;
