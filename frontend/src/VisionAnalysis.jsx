import React, { useState, useRef } from 'react';
import { Eye, Camera, Upload, X, Loader2, FileText, Scan } from 'lucide-react';

const API_BASE = '/api';

function VisionAnalysis({ onClose }) {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [prompt, setPrompt] = useState('Describe this image in detail.');
  const [provider, setProvider] = useState('gemini');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('analyze'); // 'analyze' or 'ocr'
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImage(file);
    setResult(null);
    setError(null);

    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleAnalyze = async () => {
    if (!image) return;

    setAnalyzing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', image);
    formData.append('provider', provider);
    
    const endpoint = mode === 'ocr' ? '/vision/ocr' : '/vision/analyze';
    if (mode === 'analyze') {
      formData.append('prompt', prompt);
    }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      
      if (data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Analysis failed');
      }
    } catch (err) {
      setError('Failed to analyze image');
    } finally {
      setAnalyzing(false);
    }
  };

  const promptSuggestions = [
    "Describe this image in detail",
    "What objects can you identify?",
    "What is the mood or atmosphere?",
    "Identify any text in the image",
    "What colors are dominant?",
    "Is there anything unusual?"
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl">
              <Eye className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Vision Analysis</h2>
              <p className="text-xs text-slate-400">Analyze images with AI</p>
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
          {/* Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setMode('analyze')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                mode === 'analyze' 
                  ? 'bg-cyan-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Eye className="w-4 h-4" />
              Analyze
            </button>
            <button
              onClick={() => setMode('ocr')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                mode === 'ocr' 
                  ? 'bg-cyan-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Scan className="w-4 h-4" />
              Extract Text (OCR)
            </button>
          </div>

          {/* Upload Section */}
          <div className="bg-slate-700/50 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Upload className="w-5 h-5" /> Upload Image
            </h3>
            
            {!imagePreview ? (
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-cyan-500 transition-colors"
              >
                <Camera className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-300">Click to upload an image</p>
                <p className="text-slate-500 text-sm mt-1">JPG, PNG, GIF, WEBP supported</p>
              </div>
            ) : (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-h-64 mx-auto rounded-lg"
                />
                <button
                  onClick={() => {
                    setImage(null);
                    setImagePreview(null);
                    setResult(null);
                  }}
                  className="absolute top-2 right-2 p-1 bg-red-500 rounded-full"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Analysis Options */}
          {imagePreview && mode === 'analyze' && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3">What would you like to know?</h3>
              
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask a question about this image..."
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500"
              />
              
              <div className="flex flex-wrap gap-2 mt-3">
                {promptSuggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setPrompt(suggestion)}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Provider Selection */}
          {imagePreview && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm text-slate-400">AI Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="ml-3 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                  >
                    <option value="gemini">Google Gemini</option>
                    <option value="openai">OpenAI GPT-4 Vision</option>
                  </select>
                </div>
                
                <button
                  onClick={handleAnalyze}
                  disabled={!image || analyzing}
                  className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-600 rounded-xl transition-colors flex items-center gap-2 font-medium"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      {mode === 'ocr' ? <Scan className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      {mode === 'ocr' ? 'Extract Text' : 'Analyze'}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="bg-slate-700/50 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <FileText className="w-5 h-5" /> 
                {mode === 'ocr' ? 'Extracted Text' : 'Analysis Result'}
              </h3>
              <div className="bg-slate-800 rounded-lg p-4">
                <p className="text-slate-300 whitespace-pre-wrap">{result.analysis}</p>
                <div className="mt-3 pt-3 border-t border-slate-700">
                  <span className="text-xs text-slate-500">
                    Analyzed by {result.model}
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
        </div>
      </div>
    </div>
  );
}

export default VisionAnalysis;
