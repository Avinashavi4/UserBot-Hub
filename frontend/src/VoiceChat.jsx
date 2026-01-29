import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Globe, BookOpen, X, Play, Square, Settings, MessageCircle } from 'lucide-react';

const API_BASE = '/api';

// Supported languages - grouped by region
const LANGUAGES = [
  // English
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'en-gb', name: 'English (UK)', flag: '🇬🇧' },
  
  // Indian Languages
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
  { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
  { code: 'ml', name: 'Malayalam', flag: '🇮🇳' },
  { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
  { code: 'ur', name: 'Urdu', flag: '🇵🇰' },
  
  // European Languages
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺' },
  { code: 'nl', name: 'Dutch', flag: '🇳🇱' },
  { code: 'pl', name: 'Polish', flag: '🇵🇱' },
  
  // Asian Languages
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'zh', name: 'Mandarin', flag: '🇨🇳' },
  { code: 'th', name: 'Thai', flag: '🇹🇭' },
  { code: 'vi', name: 'Vietnamese', flag: '🇻🇳' },
  { code: 'id', name: 'Indonesian', flag: '🇮🇩' },
  
  // Middle Eastern
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
  { code: 'he', name: 'Hebrew', flag: '🇮🇱' },
  { code: 'tr', name: 'Turkish', flag: '🇹🇷' },
];

// Audio Visualizer Component
function AudioVisualizer({ audioContext, sourceNode, isActive, label }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const analyserRef = useRef(null);

  useEffect(() => {
    if (!audioContext || !sourceNode || !isActive) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      return;
    }

    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    sourceNode.connect(analyser);
    analyserRef.current = analyser;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.fillStyle = 'rgba(17, 24, 39, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        
        const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, '#8B5CF6');
        gradient.addColorStop(1, '#6366F1');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioContext, sourceNode, isActive]);

  return (
    <div className="flex flex-col items-center">
      <canvas
        ref={canvasRef}
        width={120}
        height={60}
        className="rounded-lg bg-gray-900/50"
      />
      <span className="text-xs text-gray-400 mt-1">{label}</span>
    </div>
  );
}

// Live Transcript Component
function LiveTranscript({ transcripts }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [transcripts]);

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto p-4 space-y-3"
    >
      {transcripts.map((t, idx) => (
        <div
          key={idx}
          className={`flex ${t.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] px-4 py-2 rounded-2xl ${
              t.role === 'user'
                ? 'bg-purple-600 text-white rounded-br-md'
                : 'bg-gray-700 text-gray-100 rounded-bl-md'
            } ${t.isTemp ? 'opacity-60' : ''}`}
          >
            <p className="text-sm">{t.text}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// Mission Card Component
function MissionCard({ mission, selected, onSelect }) {
  return (
    <button
      onClick={() => onSelect(mission)}
      className={`p-4 rounded-xl border-2 transition-all text-left ${
        selected?.id === mission.id
          ? 'border-purple-500 bg-purple-500/10'
          : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'
      }`}
    >
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{mission.icon}</span>
        <div>
          <h3 className="font-semibold text-white">{mission.title}</h3>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            mission.difficulty === 'beginner' ? 'bg-green-500/20 text-green-400' :
            mission.difficulty === 'intermediate' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          }`}>
            {mission.difficulty}
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-400">{mission.situation}</p>
      <p className="text-xs text-gray-500 mt-2">~{mission.estimatedMinutes} min</p>
    </button>
  );
}

// Main Voice Chat Component
export default function VoiceChat({ onClose }) {
  // State
  const [view, setView] = useState('setup'); // setup, active, summary
  const [missions, setMissions] = useState([]);
  const [selectedMission, setSelectedMission] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0]);
  const [mode, setMode] = useState('teacher');
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [error, setError] = useState(null);

  // Refs
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Fetch missions on mount
  useEffect(() => {
    fetch(`${API_BASE}/missions`)
      .then(res => res.json())
      .then(setMissions)
      .catch(err => console.error('Failed to load missions:', err));
  }, []);

  // Start a voice session
  const startSession = async () => {
    try {
      setError(null);
      
      // Create session via REST API
      const res = await fetch(`${API_BASE}/voice/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mission_id: selectedMission?.id,
          language: selectedLanguage.name,
          from_language: 'English',
          mode: mode
        })
      });

      if (!res.ok) throw new Error('Failed to create session');
      
      const data = await res.json();
      setSessionId(data.session_id);

      // Connect WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/voice/${data.session_id}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setView('active');
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleWebSocketMessage(msg);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsRecording(false);
      };

    } catch (err) {
      setError(err.message);
    }
  };

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (msg) => {
    switch (msg.type) {
      case 'connected':
        console.log('Session connected:', msg.session_id);
        break;
        
      case 'input_transcript':
        // User's speech transcribed
        setTranscripts(prev => {
          const newTranscripts = [...prev];
          // Update or add user transcript
          if (msg.is_final) {
            newTranscripts.push({ role: 'user', text: msg.text, isTemp: false });
          }
          return newTranscripts;
        });
        break;
        
      case 'output_transcript':
      case 'text':
        // AI response
        const text = msg.text || msg.data;
        if (text) {
          setTranscripts(prev => [...prev, { role: 'assistant', text, isTemp: false }]);
          // Use browser TTS to speak the response
          speakText(text);
        }
        break;
        
      case 'turn_complete':
        console.log('Turn complete');
        break;
        
      case 'error':
        setError(msg.message);
        break;
        
      case 'session_ended':
        setView('summary');
        break;
    }
  };

  // Text-to-Speech using browser API
  const speakText = (text) => {
    if (isMuted || !synthRef.current) return;
    
    // Cancel any ongoing speech
    synthRef.current.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Try to find a voice for the selected language
    const voices = synthRef.current.getVoices();
    const langCode = selectedLanguage.code;
    const voice = voices.find(v => v.lang.startsWith(langCode)) || voices[0];
    if (voice) utterance.voice = voice;
    
    synthRef.current.speak(utterance);
  };

  // Start recording audio
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      audioContextRef.current = new AudioContext();
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const reader = new FileReader();
        
        reader.onloadend = () => {
          const base64 = reader.result.split(',')[1];
          
          // Send audio to WebSocket
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              data: base64,
              mime_type: 'audio/webm'
            }));
          }
        };
        
        reader.readAsDataURL(blob);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (err) {
      setError('Microphone access denied');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setIsRecording(false);
  };

  // Send text message (fallback)
  const [textInput, setTextInput] = useState('');
  
  const sendTextMessage = () => {
    if (!textInput.trim() || !wsRef.current) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'text',
      data: textInput
    }));
    
    setTranscripts(prev => [...prev, { role: 'user', text: textInput, isTemp: false }]);
    setTextInput('');
  };

  // End session
  const endSession = () => {
    stopRecording();
    synthRef.current?.cancel();
    
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end' }));
      wsRef.current.close();
    }
    
    setView('summary');
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      wsRef.current?.close();
      synthRef.current?.cancel();
    };
  }, []);

  // Render Setup View
  if (view === 'setup') {
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Globe className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl font-bold text-white">Language Learning</h1>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Language Selection */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-3">Choose a Language</h2>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map(lang => (
                <button
                  key={lang.code}
                  onClick={() => setSelectedLanguage(lang)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                    selectedLanguage.code === lang.code
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Mode Selection */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-3">Learning Mode</h2>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setMode('teacher')}
                className={`p-4 rounded-xl border-2 transition-all text-left ${
                  mode === 'teacher'
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <BookOpen className="w-6 h-6 text-purple-400 mb-2" />
                <h3 className="font-semibold text-white">Teacher Mode</h3>
                <p className="text-sm text-gray-400">Get explanations and help in English</p>
              </button>
              <button
                onClick={() => setMode('immersive')}
                className={`p-4 rounded-xl border-2 transition-all text-left ${
                  mode === 'immersive'
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <Globe className="w-6 h-6 text-purple-400 mb-2" />
                <h3 className="font-semibold text-white">Immersive Mode</h3>
                <p className="text-sm text-gray-400">Full immersion - target language only</p>
              </button>
            </div>
          </div>

          {/* Mission Selection */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-3">Choose a Mission</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {missions.map(mission => (
                <MissionCard
                  key={mission.id}
                  mission={mission}
                  selected={selectedMission}
                  onSelect={setSelectedMission}
                />
              ))}
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400 mb-4">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={startSession}
            disabled={!selectedMission}
            className="w-full py-3 px-6 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
          >
            <Play className="w-5 h-5" />
            Start Mission
          </button>
        </div>
      </div>
    );
  }

  // Render Active Session View
  if (view === 'active') {
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{selectedMission?.icon}</span>
            <div>
              <h1 className="font-semibold text-white">{selectedMission?.title}</h1>
              <p className="text-sm text-gray-400">
                {selectedLanguage.flag} {selectedLanguage.name} • {mode === 'teacher' ? '📚 Teacher' : '🎯 Immersive'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-2 rounded-lg ${isMuted ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-400'}`}
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            <button
              onClick={endSession}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              End
            </button>
          </div>
        </div>

        {/* Objectives */}
        <div className="p-4 bg-gray-800/50 border-b border-gray-800">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Objectives:</h3>
          <div className="flex flex-wrap gap-2">
            {selectedMission?.objectives.map((obj, idx) => (
              <span key={idx} className="px-3 py-1 bg-gray-700 text-gray-300 rounded-full text-sm">
                {obj}
              </span>
            ))}
          </div>
        </div>

        {/* Transcript */}
        <LiveTranscript transcripts={transcripts} />

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800 bg-gray-800/50">
          {/* Text input fallback */}
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
              placeholder="Type a message..."
              className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
            <button
              onClick={sendTextMessage}
              disabled={!textInput.trim()}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-lg"
            >
              <MessageCircle className="w-5 h-5" />
            </button>
          </div>

          {/* Mic button */}
          <div className="flex justify-center">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-6 rounded-full transition-all ${
                isRecording
                  ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                  : 'bg-purple-600 hover:bg-purple-700'
              }`}
            >
              {isRecording ? (
                <MicOff className="w-8 h-8 text-white" />
              ) : (
                <Mic className="w-8 h-8 text-white" />
              )}
            </button>
          </div>
          <p className="text-center text-sm text-gray-400 mt-2">
            {isRecording ? 'Recording... Click to stop' : 'Click to start speaking'}
          </p>
        </div>
      </div>
    );
  }

  // Render Summary View
  return (
    <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        <div className="text-6xl mb-4">🎉</div>
        <h1 className="text-2xl font-bold text-white mb-2">Mission Complete!</h1>
        <p className="text-gray-400 mb-6">{selectedMission?.title}</p>
        
        <div className="space-y-3 mb-8">
          <button
            onClick={() => {
              setView('setup');
              setTranscripts([]);
              setSelectedMission(null);
            }}
            className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Try Another Mission
          </button>
          <button
            onClick={onClose}
            className="w-full py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
          >
            Back to Chat
          </button>
        </div>
      </div>
    </div>
  );
}
