import React, { useState } from 'react';
import { Image, Sparkles, X, Loader2, Download, Wand2 } from 'lucide-react';

const API_BASE = '/api';

function ImageGenerator({ onClose }) {
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [images, setImages] = useState([]);
  const [error, setError] = useState(null);
  const [settings, setSettings] = useState({
    size: '1024x1024',
    quality: 'standard'
  });

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setGenerating(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/image/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          size: settings.size,
          quality: settings.quality
        }),
      });

      const data = await res.json();
      
      if (data.success) {
        setImages(prev => [...data.images, ...prev]);
      } else {
        setError(data.error || 'Generation failed');
      }
    } catch (err) {
      setError('Failed to generate image');
    } finally {
      setGenerating(false);
    }
  };

  const downloadImage = async (url, index) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `generated-image-${index + 1}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const examplePrompts = [
    "A serene Japanese garden with cherry blossoms and a wooden bridge",
    "A futuristic cityscape at sunset with flying cars",
    "A cozy cabin in the mountains during winter",
    "An underwater scene with colorful coral and tropical fish",
    "A magical forest with glowing mushrooms and fireflies"
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
              <Image className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Image Generator</h2>
              <p className="text-xs text-slate-400">Create images with DALL-E 3</p>
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
          {/* Prompt Input */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Wand2 className="w-5 h-5" /> Describe Your Image
            </h3>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the image you want to create in detail..."
              className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 resize-none"
              rows={3}
            />
            
            {/* Settings */}
            <div className="flex flex-wrap gap-4 mt-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">Size</label>
                <select
                  value={settings.size}
                  onChange={(e) => setSettings(s => ({ ...s, size: e.target.value }))}
                  className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm"
                >
                  <option value="1024x1024">Square (1024x1024)</option>
                  <option value="1792x1024">Landscape (1792x1024)</option>
                  <option value="1024x1792">Portrait (1024x1792)</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">Quality</label>
                <select
                  value={settings.quality}
                  onChange={(e) => setSettings(s => ({ ...s, quality: e.target.value }))}
                  className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm"
                >
                  <option value="standard">Standard</option>
                  <option value="hd">HD</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || generating}
              className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-slate-600 disabled:to-slate-600 rounded-xl transition-all flex items-center justify-center gap-2 font-medium"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Image
                </>
              )}
            </button>
          </div>

          {/* Example Prompts */}
          {images.length === 0 && !generating && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Try these prompts:</h3>
              <div className="flex flex-wrap gap-2">
                {examplePrompts.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setPrompt(example)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
                  >
                    {example.slice(0, 40)}...
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Generated Images */}
          {images.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Generated Images</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((img, idx) => (
                  <div key={idx} className="bg-slate-700/50 rounded-xl overflow-hidden">
                    <img
                      src={img.url || `data:image/png;base64,${img.base64}`}
                      alt={img.revised_prompt || 'Generated image'}
                      className="w-full aspect-square object-cover"
                    />
                    <div className="p-3">
                      {img.revised_prompt && (
                        <p className="text-sm text-slate-400 mb-2 line-clamp-2">
                          {img.revised_prompt}
                        </p>
                      )}
                      <button
                        onClick={() => downloadImage(img.url, idx)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-white transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
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

export default ImageGenerator;
