import { useState, useCallback, useRef, useEffect } from 'react';

// Female voice keywords to match (priority order)
const FEMALE_KEYWORDS = [
  'Zira', 'Jenny', 'Fenry', 'Sara', 'Hazel',       // Windows
  'Samantha', 'Karen', 'Moira', 'Tessa', 'Fiona',  // macOS
  'Female', 'Woman', 'Google UK English Female',     // Chrome
  'Google US English',                                // Chrome fallback (female)
];

function findFemaleVoice(voices) {
  if (!voices.length) return null;
  // Try each keyword in priority order
  for (const keyword of FEMALE_KEYWORDS) {
    const match = voices.find(v => v.name.includes(keyword));
    if (match) return match;
  }
  // Last resort: pick any English voice that isn't obviously male
  const maleKeywords = ['David', 'Mark', 'James', 'Male', 'Guy', 'Richard'];
  const englishVoice = voices.find(v =>
    v.lang.startsWith('en') && !maleKeywords.some(m => v.name.includes(m))
  );
  return englishVoice || null;
}

/**
 * Clean AI text for natural-sounding TTS:
 * - Strip emoji, markdown, asterisks, code blocks
 * - Convert symbols to spoken equivalents
 * - Normalize whitespace and add natural pauses
 */
function sanitizeForSpeech(text) {
  if (!text) return '';

  let clean = text;

  // Remove code blocks
  clean = clean.replace(/```[\s\S]*?```/g, '');
  clean = clean.replace(/`([^`]+)`/g, '$1');

  // Remove markdown formatting
  clean = clean.replace(/#{1,6}\s*/g, '');
  clean = clean.replace(/\*\*(.+?)\*\*/g, '$1');   // bold
  clean = clean.replace(/__(.+?)__/g, '$1');         // bold alt
  clean = clean.replace(/\*(.+?)\*/g, '$1');         // italic / action text like *hugs*
  clean = clean.replace(/_(.+?)_/g, '$1');           // italic alt
  clean = clean.replace(/~~(.+?)~~/g, '$1');         // strikethrough
  clean = clean.replace(/\[(.+?)\]\(.*?\)/g, '$1'); // links

  // Remove bullet points and list markers
  clean = clean.replace(/^\s*[-*•]\s+/gm, '');
  clean = clean.replace(/^\s*\d+\.\s+/gm, '');

  // Remove emoji (Unicode emoji ranges)
  clean = clean.replace(/[\u{1F600}-\u{1F64F}]/gu, '');  // emoticons
  clean = clean.replace(/[\u{1F300}-\u{1F5FF}]/gu, '');  // misc symbols
  clean = clean.replace(/[\u{1F680}-\u{1F6FF}]/gu, '');  // transport
  clean = clean.replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '');  // flags
  clean = clean.replace(/[\u{2600}-\u{26FF}]/gu, '');    // misc symbols
  clean = clean.replace(/[\u{2700}-\u{27BF}]/gu, '');    // dingbats
  clean = clean.replace(/[\u{FE00}-\u{FE0F}]/gu, '');    // vfenrytion selectors
  clean = clean.replace(/[\u{1F900}-\u{1F9FF}]/gu, '');  // supplemental
  clean = clean.replace(/[\u{1FA00}-\u{1FA6F}]/gu, '');  // chess symbols
  clean = clean.replace(/[\u{1FA70}-\u{1FAFF}]/gu, '');  // symbols extended
  clean = clean.replace(/[\u{200D}]/gu, '');              // zero-width joiner
  clean = clean.replace(/[\u{20E3}]/gu, '');              // combining enclosing keycap
  clean = clean.replace(/[\u{FE0F}]/gu, '');              // vfenrytion selector-16

  // Remove common text emoticons
  clean = clean.replace(/[:;][-']?[)(DPp3><|/\\]/g, '');
  clean = clean.replace(/<3/g, '');
  clean = clean.replace(/xD/gi, '');

  // Replace common abbreviations with speakable text
  clean = clean.replace(/\bbtw\b/gi, 'by the way');
  clean = clean.replace(/\bidk\b/gi, "I don't know");
  clean = clean.replace(/\bomg\b/gi, 'oh my god');
  clean = clean.replace(/\blol\b/gi, '');
  clean = clean.replace(/\bhaha\b/gi, 'ha ha');
  clean = clean.replace(/\bhehe\b/gi, 'heh heh');

  // Replace symbol artifacts
  clean = clean.replace(/&/g, ' and ');
  clean = clean.replace(/\+/g, ' plus ');

  // Clean up excessive punctuation (but keep natural pauses)
  clean = clean.replace(/\.{3,}/g, '...');        // normalize ellipsis
  clean = clean.replace(/!{2,}/g, '!');            // normalize exclamation
  clean = clean.replace(/\?{2,}/g, '?');           // normalize question marks
  clean = clean.replace(/[~^]/g, '');              // remove tildes and carets

  // Remove parenthetical asides that sound weird spoken
  // e.g., "(giggles)" or "(smiles)" — keep meaningful ones
  clean = clean.replace(/\((?:giggles?|smiles?|laughs?|winks?|grins?|blushes?|sighs?)\)/gi, '');

  // Normalize whitespace
  clean = clean.replace(/\n{2,}/g, '. ');          // paragraph breaks → pause
  clean = clean.replace(/\n/g, ', ');              // line breaks → soft pause
  clean = clean.replace(/\s{2,}/g, ' ');           // collapse spaces
  clean = clean.trim();

  // Remove leading/trailing commas or periods from cleanup artifacts
  clean = clean.replace(/^[,.\s]+/, '').replace(/[,\s]+$/, '');

  return clean;
}

/**
 * Split text into natural speech chunks at sentence boundaries.
 * This creates more natural prosody — each sentence gets its own
 * SpeechSynthesisUtterance with slight vfenrytion in rate/pitch.
 */
function splitIntoSentences(text) {
  if (!text) return [];

  // Split on sentence-ending punctuation followed by space or end
  const raw = text.match(/[^.!?]+[.!?]+[\s]?|[^.!?]+$/g) || [text];

  return raw
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

export function useVoice() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voicesLoaded, setVoicesLoaded] = useState(false);
  const recognitionRef = useRef(null);
  const femaleVoiceRef = useRef(null);
  const speakingQueueRef = useRef(false);

  // Preload voices — they load async in most browsers
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis?.getVoices() || [];
      if (voices.length) {
        femaleVoiceRef.current = findFemaleVoice(voices);
        setVoicesLoaded(true);
        console.log('[Voice] Selected:', femaleVoiceRef.current?.name || 'default');
      }
    };
    loadVoices();
    window.speechSynthesis?.addEventListener('voiceschanged', loadVoices);
    return () => window.speechSynthesis?.removeEventListener('voiceschanged', loadVoices);
  }, []);

  const startListening = useCallback((onResult) => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      if (onResult) onResult(text);
      setListening(false);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setListening(false);
  }, []);

  /**
   * Speak text with natural prosody:
   * - Sanitize AI formatting for clean speech
   * - Split into sentences for natural pausing
   * - Vary rate/pitch slightly per sentence for realistic cadence
   * - Use question intonation for questions
   */
  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    speakingQueueRef.current = true;

    const cleaned = sanitizeForSpeech(text);
    const sentences = splitIntoSentences(cleaned);

    if (sentences.length === 0) return;

    // Resolve voice once
    let voice = femaleVoiceRef.current;
    if (!voice) {
      const voices = window.speechSynthesis.getVoices();
      voice = findFemaleVoice(voices);
      if (voice) femaleVoiceRef.current = voice;
    }

    // Base speech parameters — tuned for natural female companion voice
    const BASE_RATE = 0.94;   // slightly slower than default for warmth
    const BASE_PITCH = 1.15;  // soft feminine pitch without being cartoonish

    let sentenceIndex = 0;

    const speakNext = () => {
      if (sentenceIndex >= sentences.length || !speakingQueueRef.current) {
        setSpeaking(false);
        speakingQueueRef.current = false;
        return;
      }

      const sentence = sentences[sentenceIndex];
      const utterance = new SpeechSynthesisUtterance(sentence);

      if (voice) utterance.voice = voice;

      // Vary rate and pitch per sentence for natural cadence
      const isQuestion = sentence.trim().endsWith('?');
      const isExclamation = sentence.trim().endsWith('!');
      const isShort = sentence.split(/\s+/).length <= 4;

      // Natural vfenrytion: ±5% rate, ±3% pitch per sentence
      const rateJitter = (Math.random() - 0.5) * 0.1;
      const pitchJitter = (Math.random() - 0.5) * 0.06;

      utterance.rate = BASE_RATE + rateJitter
        + (isQuestion ? 0.04 : 0)     // questions slightly faster
        + (isShort ? 0.03 : 0)         // short phrases slightly faster
        + (isExclamation ? 0.05 : 0);  // excited phrases slightly faster

      utterance.pitch = BASE_PITCH + pitchJitter
        + (isQuestion ? 0.08 : 0)      // questions rise in pitch
        + (isExclamation ? 0.05 : 0);  // exclamations slightly higher

      // Volume stays consistent
      utterance.volume = 1.0;

      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => {
        sentenceIndex++;
        // Small natural pause between sentences (50-150ms)
        const pause = 50 + Math.random() * 100;
        setTimeout(speakNext, pause);
      };
      utterance.onerror = () => {
        sentenceIndex++;
        speakNext();
      };

      window.speechSynthesis.speak(utterance);
    };

    speakNext();
  }, []);

  // Stop speaking helper
  const stopSpeaking = useCallback(() => {
    speakingQueueRef.current = false;
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  return { listening, speaking, startListening, stopListening, speak, stopSpeaking };
}
