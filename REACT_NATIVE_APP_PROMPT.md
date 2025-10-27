# React Native App Development Prompt - Ask Rumi

## Project Overview
Build a complete React Native mobile application for "Ask Rumi" - a spiritual AI mentor app that converses as the Persian poet and mystic Jalaluddin Rumi. The app should provide a beautiful, intuitive interface for users to engage in meaningful conversations with an AI that responds in Rumi's poetic and wise style.

## Technical Stack
- **Framework:** React Native (latest version)
- **Metro Bundler:** For JavaScript bundling
- **Navigation:** React Navigation (Stack Navigator for page navigation)
- **State Management:** React Context API + useState/useEffect hooks
- **UI Components:** React Native built-in components with custom styling
- **API:** Axios or Fetch for HTTP requests
- **Storage:** AsyncStorage for local settings persistence
- **TTS:** React Native Text-to-Speech library (optional)
- **Language:** TypeScript (preferred) or JavaScript

## Backend API Base URL
```
http://127.0.0.1:8001
```

## Core Application Structure

### Main Navigation (Tab Navigator or Stack Navigator)
The app should have 6 main sections accessible via navigation tabs:

1. **💬 Chat** - Main conversation interface
2. **🤖 Models** - Display available AI models
3. **📊 System** - Show system information
4. **📚 History** - List of past conversations
5. **⚙️ Settings** - Audio, appearance, model preferences
6. **🧠 LLM Settings** - Advanced AI behavior configuration

## Detailed Implementation Guide

### 1. Chat Screen (💬)
**Purpose:** Main conversation interface where users chat with Rumi

**Features:**
- Message list with user and bot avatars (👤 for user, 🧠 for bot)
- Chat input at bottom with send button and voice input (🎤)
- Real-time message display with typing indicators
- Message bubbles with different styling for user vs Rumi
- Action buttons on each message: 🔊 (speak) and 📋 (copy)
- Model selector in header (Gemma 3, Qwen 3)
- Clear chat button (🗑️) and New Chat button (✨)

**API Endpoint:**
```
POST /api/chat/ask-rumi
Body: {
  "message": "user message text",
  "model": "gemma3:270m",
  "temperature": 0.8,
  "conversation_id": "optional_conversation_id"
}

Response: {
  "response": "Rumi's response text",
  "conversation_id": "conv_123",
  "inference_time": 0.97,
  "timestamp": "2025-10-27T19:01:37"
}
```

**Response Format:**
The response includes technical specs at the end like:
```
"Hello! How are you today?"

--- TECH SPECS ---
Mode: 💬 Casual Chat
Quotes used: 0
Time: 0.47s
```

Or for wisdom responses:
```
"Your life is not a journey to the grave..."

--- TECH SPECS ---
Mode: 🔮 Rumi Wisdom
Quotes used: 3
Time: 2.33s
📜 Sources: SPH011, DLV003, DLV010
```

**UI Components Needed:**
- FlatList or ScrollView for message container
- MessageBubble component (custom)
- ChatInput component with multiline text input
- Voice recording button
- Send button
- Header with model selector

**Styling:**
- User messages: accent color background, right-aligned
- Bot messages: light background, left-aligned
- Rounded message bubbles
- Avatar icons (👤 for user, 🧠 for bot)
- Smooth animations for new messages

### 2. Models Screen (🤖)
**Purpose:** Display available AI models with status and details

**API Endpoint:**
```
GET /api/models/
Response: {
  "models": [
    {
      "name": "gemma3:270m",
      "display_name": "Gemma 3",
      "description": "Fast and efficient model...",
      "size_gb": 0.5,
      "provider": "Ollama",
      "status": "available"
    }
  ]
}
```

**Features:**
- Grid or list of model cards
- Show model name, size, provider, status
- Color-coded status (green = available, red = not available)
- Select button for available models
- Download button for unavailable models
- Test button to test model functionality
- Visual distinction for currently selected model

**UI Requirements:**
- Card-based layout
- Status badges
- Model information display
- Action buttons (Select/Download/Test)
- Highlighted selected model

### 3. System Screen (📊)
**Purpose:** Display system information and status

**API Endpoint:**
```
GET /api/system/info
Response: {
  "platform": "Darwin",
  "python_version": "3.11.0",
  "torch_version": "2.1.0",
  "cpu_count": 8,
  "memory_total": 16.0,
  "memory_available": 8.5
}
```

**Features:**
- Display system stats in cards:
  - Platform/OS
  - Python version
  - PyTorch version
  - CPU cores
  - Total memory
  - Available memory
- Grid layout for stats
- Large numbers with labels
- Clean, informative design

### 4. History Screen (📚)
**Purpose:** View and manage past conversations

**API Endpoints:**
```
GET /api/chat/conversations
Response: {
  "conversations": [
    {
      "id": "conv_123",
      "created_at": "2025-10-27T10:00:00",
      "updated_at": "2025-10-27T11:00:00",
      "message_count": 15,
      "model": "gemma3:270m",
      "messages": [...]
    }
  ]
}

DELETE /api/chat/conversations/{conversation_id}
```

**Features:**
- Sidebar with conversation list
- Main content area to display conversation when selected
- Each conversation item shows:
  - Title/ID
  - Last updated date
  - Message count
  - Preview of first user message
  - Model used
- Delete button (🗑️) on each conversation
- Click conversation to load and display messages
- Swipe to delete (optional enhancement)

**UI Components:**
- Sidebar container (30% width)
- Conversation list (FlatList)
- Conversation item cards
- Main content area (70% width)
- Message display when conversation selected
- Empty state when no conversation selected

### 5. Settings Screen (⚙️)
**Purpose:** User preferences for app behavior

**Features (Three Sections):**

#### 🔊 Audio Settings
- Text-to-Speech toggle (Automatically speak Rumi's responses)
  - Boolean toggle switch
- Voice Input toggle (Allow voice input for questions)
  - Boolean toggle switch

#### 🎨 Appearance
- Dark Mode toggle
  - Switches between light/dark theme
  - Persist preference

#### 🤖 Model Settings
- Default Model selector
  - Dropdown/Picker with available models
  - Options: Gemma 3 (Fast), Qwen 3 (Balanced)

**Storage:**
- Use AsyncStorage to persist user preferences
- Load settings on app start
- Apply settings globally

**UI Components:**
- Section headers
- Toggle switches (custom or library)
- Selector/Picker component
- Save button (if needed, or auto-save)

### 6. LLM Settings Screen (🧠)
**Purpose:** Advanced configuration for AI behavior

**API Endpoints:**
```
GET /api/chat/behavior-settings
Response: {
  "status": "success",
  "config": {
    "conversation_history_depth": 2,
    "max_tokens_wisdom": 300,
    "max_tokens_empathetic": 280,
    "max_tokens_casual": 220,
    "temperature": 0.8,
    "max_quotes_retrieved": 3,
    "prompt_templates": {...},
    "quote_formatting": {...},
    "response_guidelines": {...},
    "post_processing": {...}
  }
}

POST /api/chat/behavior-settings
Body: { /* updated config object */ }
```

**Features (Two Sections):**

#### ⚙️ Basic Behavior Settings
Input fields with number pickers:
1. **Conversation History Depth** (1-5)
   - How many previous messages to remember
   
2. **Max Tokens (Wisdom Mode)** (100-500)
   - Token limit for Rumi wisdom responses
   
3. **Max Tokens (Empathetic Mode)** (100-500)
   - Token limit for empathetic responses
   
4. **Max Tokens (Casual Mode)** (50-350)
   - Token limit for casual chat
   
5. **Temperature** (0.0-1.0, step 0.1)
   - Response creativity
   
6. **Max Quotes Retrieved** (1-5)
   - Number of quotes to use from knowledge base

**Save button:** 💾 Save LLM Behavior Settings

#### 📝 Prompt Templates (JSON Editor)
- Large text area with monospace font
- Pre-populated with JSON config structure
- Editable JSON for:
  - Prompt templates (casual, empathetic, wisdom)
  - Quote formatting settings
  - Response guidelines
  - Post-processing rules

**Buttons:**
- 💾 Save Prompt Templates
- 🔄 Reset to Default

**JSON Structure to Display:**
```json
{
  "prompt_templates": {
    "casual": {
      "role": "friendly, approachable person",
      "instructions": "...",
      "word_limit": [60, 180],
      "prompt_template": "..."
    },
    "empathetic": {...},
    "wisdom": {...}
  },
  "quote_formatting": {...},
  "response_guidelines": {...},
  "post_processing": {...}
}
```

**UI Requirements:**
- Scrollable container for both sections
- Number inputs with min/max/step validation
- Large textarea for JSON editor
- Syntax highlighting (optional, can use library)
- Clear labels and descriptions
- Save feedback (toast notifications)

## Design Specifications

### Color Scheme
- **Primary:** #667eea (Purple)
- **Secondary:** #764ba2 (Darker purple)
- **Accent:** #ff6b6b (Coral red)
- **Text:** #333 (Dark gray)
- **Background:** #f8f9fa (Light gray)
- **Card Background:** #ffffff (White)
- **Border:** #e9ecef (Light border)

### Typography
- **Font Family:** System default (San Francisco for iOS, Roboto for Android)
- **Headings:** 1.5rem, bold
- **Body:** 1rem, regular
- **Small:** 0.9rem, regular
- **Monospace:** For JSON editor (Courier New or Fira Code)

### Spacing
- **Container padding:** 1.5rem
- **Card padding:** 1.5rem
- **Element gap:** 1rem
- **Border radius:** 8px (buttons), 12px (cards), 16px (containers)

### Shadows
- **Light:** 0 2px 4px rgba(0,0,0,0.1)
- **Medium:** 0 4px 6px rgba(0,0,0,0.1)
- **Large:** 0 10px 25px rgba(0,0,0,0.15)

## Key Features to Implement

### 1. Message Display with Animations
- Messages slide in from left (bot) or right (user)
- Typing indicator while waiting for response
- Message actions appear on tap/long-press
- Smooth scrolling to bottom on new message

### 2. Voice Input
- Microphone button in input area
- Recording state visual feedback (pulsing red)
- Transcribe speech to text
- Handle errors gracefully

### 3. Text-to-Speech
- 🔊 button on each message
- Speak message content
- Pause/stop functionality
- Handle speaking state

### 4. Copy to Clipboard
- 📋 button on each message
- Copy message text
- Show toast notification on success

### 5. Message Actions
- Long press message for context menu
- Options: Copy, Speak, Delete (user only)
- Visual feedback on actions

### 6. Loading States
- Chat input disabled while processing
- Typing indicator
- Loading spinner for API calls
- Error handling with retry

### 7. Toast Notifications
- Success (green)
- Error (red)
- Info (blue)
- Auto-dismiss after 3 seconds
- Slide in from top/bottom

### 8. Keyboard Handling
- Auto-resize text input
- Scroll to input when keyboard appears
- Dismiss keyboard on scroll
- Handle keyboard height properly

## API Integration Patterns

### API Client Setup
```typescript
// Create API client
const API_BASE = Platform.select({
  ios: 'http://localhost:8001',
  android: 'http://10.0.2.2:8001',
  default: 'http://127.0.0.1:8001'
});

// Helper function for API calls
async function apiCall(endpoint: string, options?: RequestInit) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### Error Handling
- Network errors
- Timeout handling
- Retry logic for failed requests
- User-friendly error messages
- Offline detection

### Loading States
- Show loading indicators
- Disable buttons during requests
- Prevent duplicate requests
- Smooth state transitions

## State Management

### Context Setup
```typescript
// AppContext.ts
interface AppState {
  selectedModel: string;
  settings: UserSettings;
  conversations: Conversation[];
  currentConversation: Conversation | null;
}

interface AppContextValue {
  state: AppState;
  updateModel: (model: string) => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
  addMessage: (message: Message) => void;
  loadConversations: () => Promise<void>;
}
```

### UserSettings Interface
```typescript
interface UserSettings {
  tts: boolean;
  voiceInput: boolean;
  darkMode: boolean;
  defaultModel: string;
}
```

## Navigation Structure

### Recommended Setup
Use React Navigation with Tab Navigator for main sections:

```
App
├── TabNavigator
│   ├── ChatTab
│   │   └── ChatScreen
│   ├── ModelsTab
│   │   └── ModelsScreen
│   ├── SystemTab
│   │   └── SystemScreen
│   ├── HistoryTab
│   │   └── HistoryScreen
│   ├── SettingsTab
│   │   └── SettingsScreen
│   └── LLMSettingsTab
│       └── LLMSettingsScreen
```

## Platform-Specific Considerations

### iOS
- Use SafeAreaView for proper layout
- Handle notches and home indicator
- App Store guidelines compliance
- Native navigation transitions

### Android
- Handle status bar height
- Use elevation instead of shadows
- Handle back button properly
- Material Design elements

## Performance Optimizations

1. **Memoization**
   - Use React.memo for message components
   - Memoize expensive calculations
   - Cache API responses

2. **List Optimization**
   - Use FlatList with proper keyExtractor
   - Implement virtualization
   - Pagination for conversation history

3. **Image/Icon Optimization**
   - Use vector icons where possible
   - Lazy load images
   - Cache frequently used assets

4. **Bundle Size**
   - Code splitting
   - Tree shaking
   - Remove unused dependencies

## Testing Requirements

### Unit Tests
- API client functions
- Message formatting logic
- Settings persistence
- Date formatting

### Integration Tests
- API calls
- Navigation flow
- State management
- User interactions

### Manual Testing Checklist
- [ ] Send message and receive response
- [ ] Voice input works
- [ ] Text-to-speech works
- [ ] Settings persist
- [ ] Load conversation history
- [ ] Delete conversation
- [ ] Switch models
- [ ] View system info
- [ ] Edit LLM settings
- [ ] Save prompt templates
- [ ] Copy message to clipboard
- [ ] Dark mode toggle
- [ ] Handle network errors
- [ ] Offline detection

## Additional Features to Implement

1. **Pull to Refresh**
   - Refresh conversations list
   - Refresh models list

2. **Search**
   - Search in conversation history
   - Filter by date, model, keyword

3. **Export**
   - Export conversation as text
   - Share conversation

4. **Themes**
   - Light mode
   - Dark mode
   - Custom colors

5. **Notifications**
   - Push notifications for responses
   - Badge count for unread

6. **Analytics**
   - Track message count
   - Track conversation duration
   - Track model usage

## File Structure Recommendation

```
src/
├── App.tsx
├── navigation/
│   ├── AppNavigator.tsx
│   └── TabNavigator.tsx
├── screens/
│   ├── ChatScreen.tsx
│   ├── ModelsScreen.tsx
│   ├── SystemScreen.tsx
│   ├── HistoryScreen.tsx
│   ├── SettingsScreen.tsx
│   └── LLMSettingsScreen.tsx
├── components/
│   ├── MessageBubble.tsx
│   ├── ChatInput.tsx
│   ├── Toast.tsx
│   ├── LoadingSpinner.tsx
│   └── ModelCard.tsx
├── contexts/
│   ├── AppContext.tsx
│   └── SettingsContext.tsx
├── services/
│   ├── api.ts
│   ├── storage.ts
│   └── textToSpeech.ts
├── types/
│   ├── index.ts
│   └── api.ts
├── utils/
│   ├── formatting.ts
│   └── validation.ts
└── constants/
    ├── colors.ts
    └── config.ts
```

## Implementation Priority

### Phase 1: Core Functionality
1. Navigation setup
2. Chat screen with basic messaging
3. API integration
4. Message display

### Phase 2: Enhanced Chat
5. Voice input
6. Text-to-speech
7. Copy functionality
8. Message actions

### Phase 3: Additional Screens
9. Models screen
10. System screen
11. History screen
12. Settings screens

### Phase 4: Polish
13. Animations
14. Error handling
15. Loading states
16. Toast notifications
17. Dark mode
18. Responsive design

## Success Criteria

The app is considered complete when:
- ✅ All screens are implemented and functional
- ✅ API integration works for all endpoints
- ✅ Settings persist across app restarts
- ✅ Voice input and TTS work properly
- ✅ Message history loads and displays correctly
- ✅ All user interactions provide feedback
- ✅ Error states are handled gracefully
- ✅ App performs well on both iOS and Android
- ✅ Code is clean, organized, and maintainable

## Final Notes

This prompt provides a comprehensive blueprint for building the React Native Ask Rumi app. The design emphasizes:
- **User Experience:** Intuitive navigation, smooth animations, clear feedback
- **Code Quality:** Clean structure, proper state management, error handling
- **Performance:** Optimized rendering, efficient API calls, proper caching
- **Maintainability:** Well-organized code, clear separation of concerns, reusable components

Follow this guide to create a production-ready mobile application that provides users with a beautiful and meaningful way to engage with Rumi's wisdom.

