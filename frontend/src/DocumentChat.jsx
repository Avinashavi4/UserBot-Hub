import React, { useState, useRef } from 'react';
import { FileText, Upload, Search, Trash2, X, Loader2, File, MessageCircle } from 'lucide-react';

const API_BASE = '/api';

function DocumentChat({ onClose }) {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', 'default');

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      
      if (data.success) {
        setDocuments(prev => [...prev, {
          id: data.doc_id,
          name: file.name,
          chunks: data.chunks,
          uploaded: new Date().toISOString()
        }]);
        fetchDocuments();
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (err) {
      setError('Failed to upload document');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents/list?collection=default`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    setQuerying(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/documents/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          collection: 'default',
          top_k: 5
        }),
      });

      const data = await res.json();
      
      if (data.success) {
        setResults(data);
      } else {
        setError(data.error || 'Query failed');
      }
    } catch (err) {
      setError('Failed to query documents');
    } finally {
      setQuerying(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await fetch(`${API_BASE}/documents/${docId}?collection=default`, {
        method: 'DELETE',
      });
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  React.useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Document Chat</h2>
              <p className="text-xs text-slate-400">Upload documents and ask questions</p>
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
          {/* Upload Section */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Upload className="w-5 h-5" /> Upload Documents
            </h3>
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-green-500 transition-colors"
            >
              {uploading ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-6 h-6 animate-spin text-green-400" />
                  <span className="text-slate-300">Uploading...</span>
                </div>
              ) : (
                <>
                  <File className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p className="text-slate-300">Click to upload PDF, TXT, or MD files</p>
                  <p className="text-slate-500 text-sm mt-1">Documents will be chunked and embedded for search</p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {/* Documents List */}
          {documents.length > 0 && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Uploaded Documents ({documents.length})</h3>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between bg-slate-800 rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-green-400" />
                      <div>
                        <p className="text-white font-medium">{doc.name || doc.id}</p>
                        <p className="text-xs text-slate-400">{doc.chunks || '?'} chunks</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Query Section */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <MessageCircle className="w-5 h-5" /> Ask a Question
            </h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                placeholder="What would you like to know about your documents?"
                className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-green-500"
              />
              <button
                onClick={handleQuery}
                disabled={!query.trim() || querying}
                className="px-6 py-3 bg-green-600 hover:bg-green-500 disabled:bg-slate-600 rounded-xl transition-colors flex items-center gap-2"
              >
                {querying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Results */}
          {results && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Results</h3>
              <div className="space-y-3">
                {results.results?.map((result, idx) => (
                  <div key={idx} className="bg-slate-800 rounded-lg p-4">
                    <p className="text-slate-300 text-sm">{result.content}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                      <span className="px-2 py-0.5 bg-slate-700 rounded">Score: {(result.score * 100).toFixed(1)}%</span>
                      {result.metadata?.source && <span>{result.metadata.source}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentChat;
