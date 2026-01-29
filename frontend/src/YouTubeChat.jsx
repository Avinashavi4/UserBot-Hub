import React, { useState } from 'react';
import { Youtube, MessageCircle, X, Loader2, Play, FileText } from 'lucide-react';

const API_BASE = '/api';

function YouTubeChat({ onClose }) {
  const [url, setUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [transcript, setTranscript] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [error, setError] = useState(null);

  const fetchTranscript = async () => {
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setTranscript(null);
    setAnswer(null);

    try {
      const res = await fetch(`${API_BASE}/youtube/transcript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const data = await res.json();
      
      if (data.success) {
        setTranscript(data);
      } else {
        setError(data.error || 'Failed to get transcript');
      }
    } catch (err) {
      setError('Failed to fetch transcript');
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim() || !url.trim()) return;

    setChatting(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/youtube/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          question,
        }),
      });

      const data = await res.json();
      
      if (data.success) {
        setAnswer(data);
      } else {
        setError(data.error || 'Failed to get answer');
      }
    } catch (err) {
      setError('Failed to chat about video');
    } finally {
      setChatting(false);
    }
  };

  const extractVideoId = (url) => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
      /youtube\.com\/embed\/([^&\n?#]+)/,
    ];
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const videoId = extractVideoId(url);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-red-500 to-red-600 rounded-xl">
              <Youtube className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">YouTube Chat</h2>
              <p className="text-xs text-slate-400">Chat with any YouTube video</p>
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
          {/* URL Input */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Play className="w-5 h-5" /> Enter YouTube URL
            </h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && fetchTranscript()}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-red-500"
              />
              <button
                onClick={fetchTranscript}
                disabled={!url.trim() || loading}
                className="px-6 py-3 bg-red-600 hover:bg-red-500 disabled:bg-slate-600 rounded-xl transition-colors flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileText className="w-5 h-5" />}
                <span>Get Transcript</span>
              </button>
            </div>
          </div>

          {/* Video Preview */}
          {videoId && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <div className="aspect-video w-full max-w-2xl mx-auto rounded-lg overflow-hidden">
                <iframe
                  src={`https://www.youtube.com/embed/${videoId}`}
                  title="YouTube video"
                  className="w-full h-full"
                  allowFullScreen
                />
              </div>
              {transcript && (
                <div className="mt-4 text-center">
                  <h4 className="text-white font-medium">{transcript.title}</h4>
                  <p className="text-slate-400 text-sm">
                    Duration: {Math.round(transcript.duration / 60)} minutes • {transcript.language}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Transcript Preview */}
          {transcript && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <FileText className="w-5 h-5" /> Transcript Preview
              </h3>
              <div className="max-h-40 overflow-y-auto bg-slate-800 rounded-lg p-3 text-slate-300 text-sm">
                {transcript.transcript?.slice(0, 500)}...
              </div>
            </div>
          )}

          {/* Question Input */}
          {transcript && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <MessageCircle className="w-5 h-5" /> Ask About This Video
              </h3>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                  placeholder="What is this video about? What are the key points?"
                  className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-red-500"
                />
                <button
                  onClick={askQuestion}
                  disabled={!question.trim() || chatting}
                  className="px-6 py-3 bg-red-600 hover:bg-red-500 disabled:bg-slate-600 rounded-xl transition-colors flex items-center gap-2"
                >
                  {chatting ? <Loader2 className="w-5 h-5 animate-spin" /> : <MessageCircle className="w-5 h-5" />}
                </button>
              </div>
            </div>
          )}

          {/* Answer */}
          {answer && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Answer</h3>
              <div className="bg-slate-800 rounded-lg p-4">
                <p className="text-slate-300 whitespace-pre-wrap">{answer.answer}</p>
                <div className="mt-3 pt-3 border-t border-slate-700">
                  <span className="text-xs text-slate-500">
                    Answered by {answer.provider}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {/* Empty State */}
          {!transcript && !error && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Youtube className="w-16 h-16 text-red-500/50 mb-4" />
              <p className="text-slate-400">Paste a YouTube URL to get started</p>
              <p className="text-slate-500 text-sm mt-1">Works with videos that have captions/subtitles</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default YouTubeChat;
