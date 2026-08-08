export type Language = 'en' | 'hi' | 'hinglish';

export interface LanguageOption {
  code: Language;
  label: string;
  nativeLabel: string;
  flag: string;
}

export const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिंदी', flag: '🇮🇳' },
  { code: 'hinglish', label: 'Hinglish', nativeLabel: 'Hindi + English', flag: '🇮🇳' },
];

type TranslationKey =
  | 'welcome.greeting'
  | 'welcome.subtitle'
  | 'welcome.startButton'
  | 'state.ready'
  | 'state.connecting'
  | 'state.listening'
  | 'state.speaking'
  | 'state.thinking'
  | 'state.ended'
  | 'trust.responsible'
  | 'trust.private'
  | 'trust.neverShare'
  | 'trust.disclaimer'
  | 'mic.required'
  | 'mic.howTo'
  | 'mic.tryAgain'
  | 'ended.title'
  | 'ended.subtitle'
  | 'ended.startAgain'
  | 'ended.messagesCount'
  | 'transcript.empty'
  | 'transcript.you'
  | 'transcript.moneybuddy'
  | 'language.label';

const translations: Record<Language, Record<TranslationKey, string>> = {
  en: {
    'welcome.greeting': 'Namaste! I\'m MoneyBuddy',
    'welcome.subtitle': 'Your AI companion for simple, responsible financial guidance',
    'welcome.startButton': 'Start Conversation',
    'state.ready': 'Ready to help',
    'state.connecting': 'Connecting to MoneyBuddy…',
    'state.listening': 'Listening to you…',
    'state.speaking': 'MoneyBuddy is speaking…',
    'state.thinking': 'Thinking…',
    'state.ended': 'Conversation ended',
    'trust.responsible': 'Responsible financial guidance',
    'trust.private': 'Your conversation is private',
    'trust.neverShare': 'Never share OTPs, PINs, passwords, or complete bank account details',
    'trust.disclaimer': 'MoneyBuddy provides guidance only and does not guarantee financial outcomes.',
    'mic.required': 'Microphone access is required to talk with MoneyBuddy.',
    'mic.howTo': 'Please allow microphone access in your browser settings and try again.',
    'mic.tryAgain': 'Try Again',
    'ended.title': 'Conversation ended',
    'ended.subtitle': 'Thank you for talking with MoneyBuddy',
    'ended.startAgain': 'Start Again',
    'ended.messagesCount': 'messages exchanged',
    'transcript.empty': 'Your conversation will appear here',
    'transcript.you': 'You',
    'transcript.moneybuddy': 'MoneyBuddy',
    'language.label': 'Language',
  },
  hi: {
    'welcome.greeting': 'नमस्ते! मैं मनीबडी हूँ',
    'welcome.subtitle': 'सरल और ज़िम्मेदार वित्तीय मार्गदर्शन के लिए आपका AI साथी',
    'welcome.startButton': 'बातचीत शुरू करें',
    'state.ready': 'मदद के लिए तैयार',
    'state.connecting': 'मनीबडी से कनेक्ट हो रहा है…',
    'state.listening': 'आपकी बात सुन रहा हूँ…',
    'state.speaking': 'मनीबडी बोल रहा है…',
    'state.thinking': 'सोच रहा हूँ…',
    'state.ended': 'बातचीत समाप्त',
    'trust.responsible': 'ज़िम्मेदार वित्तीय मार्गदर्शन',
    'trust.private': 'आपकी बातचीत निजी है',
    'trust.neverShare': 'कभी भी OTP, PIN, पासवर्ड या बैंक खाते की पूरी जानकारी साझा न करें',
    'trust.disclaimer': 'मनीबडी केवल मार्गदर्शन प्रदान करता है, वित्तीय परिणामों की गारंटी नहीं देता।',
    'mic.required': 'मनीबडी से बात करने के लिए माइक्रोफ़ोन की अनुमति आवश्यक है।',
    'mic.howTo': 'कृपया अपने ब्राउज़र सेटिंग्स में माइक्रोफ़ोन की अनुमति दें और पुनः प्रयास करें।',
    'mic.tryAgain': 'पुनः प्रयास करें',
    'ended.title': 'बातचीत समाप्त',
    'ended.subtitle': 'मनीबडी से बात करने के लिए धन्यवाद',
    'ended.startAgain': 'फिर से शुरू करें',
    'ended.messagesCount': 'संदेश',
    'transcript.empty': 'आपकी बातचीत यहाँ दिखाई देगी',
    'transcript.you': 'आप',
    'transcript.moneybuddy': 'मनीबडी',
    'language.label': 'भाषा',
  },
  hinglish: {
    'welcome.greeting': 'Namaste! Main MoneyBuddy hoon',
    'welcome.subtitle': 'Simple aur responsible financial guidance ke liye aapka AI companion',
    'welcome.startButton': 'Baat Shuru Karein',
    'state.ready': 'Help ke liye ready',
    'state.connecting': 'MoneyBuddy se connect ho raha hai…',
    'state.listening': 'Aapki baat sun raha hoon…',
    'state.speaking': 'MoneyBuddy bol raha hai…',
    'state.thinking': 'Soch raha hoon…',
    'state.ended': 'Baat khatam hui',
    'trust.responsible': 'Responsible financial guidance',
    'trust.private': 'Aapki baat private hai',
    'trust.neverShare': 'Kabhi bhi OTP, PIN, password ya bank details share na karein',
    'trust.disclaimer': 'MoneyBuddy sirf guidance deta hai, financial results ki guarantee nahi deta.',
    'mic.required': 'MoneyBuddy se baat karne ke liye microphone ki zaroorat hai.',
    'mic.howTo': 'Browser settings mein microphone allow karein aur phir try karein.',
    'mic.tryAgain': 'Phir Se Try Karein',
    'ended.title': 'Baat khatam hui',
    'ended.subtitle': 'MoneyBuddy se baat karne ke liye shukriya',
    'ended.startAgain': 'Phir Se Shuru Karein',
    'ended.messagesCount': 'messages exchange hue',
    'transcript.empty': 'Aapki baat yahaan dikhegi',
    'transcript.you': 'Aap',
    'transcript.moneybuddy': 'MoneyBuddy',
    'language.label': 'Bhaasha',
  },
};

export function getTranslation(language: Language, key: TranslationKey): string {
  return translations[language]?.[key] ?? translations.en[key] ?? key;
}
