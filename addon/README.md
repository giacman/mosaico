# Mosaico Google Sheets Add-on

AI Content Creation Co-Pilot living directly in your Google Sheets.

## ✨ Features

- **Generate Variations** - Create 3-10 text variations with different tones
- **Translate** - Context-aware translation maintaining brand voice
- **Refine** - One-click improvements (shorten, fix grammar, improve clarity)
- **Zero Friction** - Work directly in Sheets, no context switching

## 🚀 Setup

### Prerequisites

- Google Account
- Access to Google Sheets
- Mosaico backend deployed (see backend/README.md)

### Installation

1. **Create New Apps Script Project**
   - Open Google Sheets
   - Extensions → Apps Script
   - Create new project named "Mosaico"

2. **Copy Files**
   - Copy content from `src/Code.gs` to Script editor
   - Create HTML file: File → New → HTML file named "Sidebar"
   - Copy content from `src/Sidebar.html`
   - Copy `appsscript.json` configuration

3. **Configure Backend URL**
   - In `Code.gs`, update `BACKEND_URL` with your Cloud Run URL:
   ```javascript
   const BACKEND_URL = 'https://mosaico-backend-YOUR-PROJECT.run.app';
   ```

4. **Deploy**
   - Save all files
   - Click "Deploy" → "Test deployments"
   - Or deploy as add-on: "Deploy" → "New deployment"

### Usage

1. **Open Mosaico**
   - In Google Sheets: Extensions → Mosaico → Open Mosaico
   - Sidebar appears on the right

2. **Generate Variations**
   - Select a cell with text
   - Click "Load from Selected Cell"
   - Choose tone and number of variations
   - Click "Generate Variations"
   - Variations appear in cells below

3. **Translate**
   - Select text, load it
   - Choose target language
   - Translation replaces active cell

4. **Refine**
   - Select text, load it
   - Click quick action (Shorten, Fix Grammar, etc.)
   - Refined text replaces active cell

## 🎨 UI Overview

```
┌─────────────────────────┐
│ ✨ Mosaico              │
│ Your AI Co-Pilot        │
├─────────────────────────┤
│ [Generate] [Translate]  │
│ [Refine]                │
├─────────────────────────┤
│ Original Text:          │
│ ┌───────────────────┐   │
│ │ [text area]       │   │
│ └───────────────────┘   │
│ 📝 Load from Cell       │
│                         │
│ Count: [3] Tone: [Pro]  │
│                         │
│ [✨ Generate]           │
└─────────────────────────┘
```

## 🔧 Customization

### Add Custom Tones

In `Code.gs`, you can add custom tone types by updating the backend API call.

### Modify UI

Edit `Sidebar.html` to:
- Change colors/styling
- Add new features
- Modify layout

## 🐛 Troubleshooting

### "Failed to call Mosaico API"
- Check `BACKEND_URL` is correct
- Verify backend is deployed and running
- Check backend logs in Cloud Console

### "No text selected"
- Make sure you're selecting a cell with text
- Click the cell first, then click "Load from Cell"

### Rate Limit Errors
- Default: 5 requests/second
- Wait a moment and try again
- Contact admin to increase limit

## 📝 Development

### Testing Locally

1. Deploy backend locally (see backend/README.md)
2. Update `BACKEND_URL` to `http://localhost:8080`
3. Use ngrok for HTTPS: `ngrok http 8080`
4. Update URL to ngrok URL

### Logs

View logs: Apps Script editor → Executions tab

## 🚀 Deployment

### Option 1: Personal Use
- Keep as "Test deployment"
- Only you can access

### Option 2: Organization-Wide
- Deploy as workspace add-on
- Request Google Workspace admin to approve
- Users install from Google Workspace Marketplace (internal)

## 🔐 Permissions

The add-on requests:
- `spreadsheets.currentonly` - Read/write current spreadsheet
- `script.container.ui` - Show sidebar UI

## 📊 Performance

- **Latency**: ~2-3s per request (including backend)
- **Offline**: Not supported (requires backend API)
- **Concurrent**: Up to 5 requests/second (rate limited)

## 🎯 Roadmap

Future enhancements:
- [ ] Batch processing (multiple cells at once)
- [ ] Custom prompt templates
- [ ] A/B test variations
- [ ] History/undo
- [ ] Favorite variations

## 📝 License

Private - LuisaViaRoma Internal Project

