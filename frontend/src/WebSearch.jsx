import React, { useState } from 'react';
import { Search, Globe, Newspaper, ExternalLink, X, Loader2, Clock } from 'lucide-react';

const API_BASE = '/api';

function WebSearch({ onClose }) {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [searchType, setSearchType] = useState('web'); // 'web' or 'news'
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const endpoint = searchType === 'news' ? '/web/news' : '/web/search';
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          max_results: 10
        }),
      });

      const data = await res.json();
      
      if (data.success) {
        setResults(data);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch (err) {
      setError('Failed to perform search');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Web Search</h2>
              <p className="text-xs text-slate-400">Search the web in real-time</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Search Type Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setSearchType('web')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                searchType === 'web' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Globe className="w-4 h-4" />
              Web Search
            </button>
            <button
              onClick={() => setSearchType('news')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                searchType === 'news' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Newspaper className="w-4 h-4" />
              News
            </button>
          </div>

          {/* Search Input */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder={searchType === 'news' ? 'Search latest news...' : 'Search the web...'}
                className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSearch}
                disabled={!query.trim() || searching}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 rounded-xl transition-colors flex items-center gap-2"
              >
                {searching ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Results */}
          {results && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">
                  Results for "{results.query}"
                </h3>
                <span className="text-sm text-slate-400">
                  {results.results?.length || 0} results
                </span>
              </div>
              
              {results.results?.map((result, idx) => (
                <a
                  key={idx}
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-slate-700/50 hover:bg-slate-700 rounded-xl p-4 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="text-white font-medium mb-1 flex items-center gap-2">
                        {result.title}
                        <ExternalLink className="w-4 h-4 text-slate-400" />
                      </h4>
                      <p className="text-slate-400 text-sm mb-2">{result.snippet || result.body}</p>
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span className="text-blue-400">{new URL(result.url).hostname}</span>
                        {result.date && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {result.date}
                          </span>
                        )}
                      </div>
                    </div>
                    {result.image && (
                      <img 
                        src={result.image} 
                        alt="" 
                        className="w-20 h-20 object-cover rounded-lg"
                      />
                    )}
                  </div>
                </a>
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {/* No Results State */}
          {!results && !error && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Globe className="w-16 h-16 text-slate-600 mb-4" />
              <p className="text-slate-400">Enter a search query to find information</p>
              <p className="text-slate-500 text-sm mt-1">Powered by DuckDuckGo - No API key needed</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default WebSearch;
